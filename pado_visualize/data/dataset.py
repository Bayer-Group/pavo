import collections
import json
import logging
import time
import warnings
from functools import lru_cache, wraps
from pathlib import Path
from typing import Optional, Dict, Literal, List

import diskcache
import pandas as pd
from flask import abort
from pado.dataset import PadoDataset, PadoDatasetChain
from pado.metadata import PadoReserved, PadoColumn

__all__ = [
    "init_dataset",
    "get_dataset",
    "get_image_map",
    "get_metadata",
    "get_annotation_map",
    "get_prediction_map",
    "get_dataset_column_values"
]

# flask and dash unrelated data logger
_logger = logging.getLogger(__name__)


def log_access(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        _logger.info(f"{func.__name__}() called with args={args!r} kwargs={kwargs!r}")
        t0 = time.monotonic()
        result = func(*args, **kwargs)
        t1 = time.monotonic()
        _logger.info(f"{func.__name__}() took {t1-t0:0.5f} seconds")
        return result
    return wrapped


# data storage
dataset: Optional[PadoDataset] = None
image_map: Optional[Dict[str, Optional[Path]]] = None

# cache_sizes
LRU_CACHE_MAX_SIZE = 16  # these could be split up, but will do for now


@log_access
def init_dataset(
    dataset_paths: List[Path],
    persist: bool = True,
    ignore_cache: bool = False,
    cache_file: Optional[Path] = None,
) -> None:
    """initialize the pado dataset for the flask instance"""
    # NOTE: this should be done using a better cache system
    #   keep this logic here for now to continue developing the POC,
    #   and be able to refactor easily later
    global dataset, image_map

    if cache_file is None:
        if persist:
            _logger.warning("persist=True requested but cache_file is None")
        persist = False

    # normalize path
    dataset_paths = [
        Path(ds_pth).expanduser().absolute().resolve()
        for ds_pth in dataset_paths
    ]

    def load_dataset(paths):
        # there's no need to set this outside of init_dataset
        datasets = []
        for path in paths:
            try:
                datasets.append(PadoDataset(path, mode="r"))
            except FileNotFoundError:
                pass

        if not datasets:
            _logger.error("no datasets loaded")
            return None, None

        ds = PadoDatasetChain(*datasets)
        # build image_id:idx map
        im = {image_id: img.local_path for image_id, img in ds.images.items()}
        return ds, im

    if not persist:
        dataset, image_map = load_dataset(dataset_paths)

    else:
        with diskcache.Cache(str(cache_file)) as store:
            key = str(dataset_paths)  # TODO: revisit...
            if key not in store or ignore_cache:
                _logger.info("loading dataset from disk...")
                dataset, image_map = store[key] = load_dataset(dataset_paths)
            else:
                _logger.info("loading dataset from cache...")
                dataset, image_map = store[key]


def get_dataset(abort_if_none: bool = True) -> Optional[PadoDataset]:
    global dataset
    if abort_if_none and dataset is None:
        return abort(500, "missing dataset")
    return dataset


def _filter_dict_cache(func):
    """a cache decorator for the get_metadata function"""

    def to_items(f_dict):
        return tuple((k, tuple(sorted(v))) for k, v in sorted(f_dict.items()) if v)

    def to_dict(f_items):
        return dict(f_items)

    @lru_cache(maxsize=LRU_CACHE_MAX_SIZE)
    def _cached_func(filter_items):
        filter_dict = to_dict(filter_items)
        return func(filter_dict)

    @wraps(func)
    def wrapper(filter_dict):
        f_items = to_items(filter_dict)
        return _cached_func(f_items)

    return wrapper


class _JSONBoolMapping(dict):
    def __missing__(self, key):
        return "false"


@lru_cache()
@log_access
def get_annotation_map() -> Dict[str, Literal["true", "false"]]:
    ds = get_dataset()
    image_ids = ds.annotations.keys()
    m = _JSONBoolMapping.fromkeys(image_ids, "true")
    # noinspection PyTypeChecker
    return m


@lru_cache()
@log_access
def get_prediction_map():
    ds = get_dataset()

    # prepare directories
    qpzip_dir = ds.path / "qpzip"
    qpzip_dir.mkdir(exist_ok=True)
    predictions_dir = ds.path / "predictions"
    predictions_dir.mkdir(exist_ok=True)

    im = get_image_map()
    pm = _JSONBoolMapping()
    for image_prediction in predictions_dir.glob("*"):
        if not image_prediction.is_dir():
            continue
        if image_prediction.name not in im:
            continue
        pm[image_prediction.name] = "true"
    return pm


@_filter_dict_cache
@log_access
def get_metadata(
    filter_dict: Optional[Dict[str, List[str]]] = None,
) -> Optional[pd.DataFrame]:
    """return the optionally filtered metadata DataFrame"""
    ds = get_dataset(abort_if_none=False)
    if ds is None:
        return None

    df = ds.metadata.copy()
    df[PadoColumn.STUDY.subcolumn("SHORT")] = df[PadoColumn.STUDY].apply(lambda x: x[6:] if x.startswith("STUDY_") else x)
    df[PadoColumn.IMAGE.subcolumn("SHORT")] = df[PadoColumn.IMAGE].apply(lambda x: x.split("__")[-1])
    df[PadoColumn.FINDING] = df[PadoColumn.FINDING].str.title()
    df.loc[df[PadoColumn.FINDING] == "Unremarkable", PadoColumn.FINDING] = "UNREMARKABLE"
    # df["annotation"] = df[PadoColumn.IMAGE].map(get_annotation_map())
    amap = collections.defaultdict(lambda: 'false', dict.fromkeys(map("__".join, get_annotation_map()), 'true'))
    df["annotation"] = df[PadoColumn.IMAGE].map(amap)
    # df["prediction"] = df[PadoColumn.IMAGE].map(get_prediction_map())
    pmap = collections.defaultdict(lambda: 'false', dict.fromkeys(map("__".join, get_prediction_map()), 'true'))
    df["prediction"] = df[PadoColumn.IMAGE].map(pmap)

    if filter_dict:
        q_ands = []
        for column, values in filter_dict.items():
            if not values:
                continue

            # group "or"-queries
            q_ors = " or ".join(
                f"{column} == {json.dumps(value)}" for value in values
            )
            q_ands.append(f"({q_ors})")

        if q_ands:
            # group "and"-queries
            query = " and ".join(q_ands)
            print(query)
            df = df.query(query)
    return df


def get_image_map(abort_if_none: bool = True) -> Optional[Dict[str, Optional[Path]]]:
    global image_map
    if abort_if_none and image_map is None:
        return abort(500, "missing image map")
    return image_map


@log_access
def get_dataset_column_values(column, filter_dict=None) -> List[dict]:
    """get the column selections for the subset"""

    if filter_dict is None:
        filter_dict = {}
    # noinspection PyTypeChecker
    df = get_metadata(filter_dict=filter_dict)

    if column in {
        PadoReserved.DATA_SOURCE_ID,
        PadoColumn.STUDY,
        PadoColumn.ORGAN,
        PadoColumn.FINDING,
    }:
        return [
            {"label": x, "value": x}
            for x in sorted(df[column].dropna().unique(), key=str.lower)
            if isinstance(x, str) and x.strip()
        ]

    elif column == "annotation":
        return [
            {"label": "with Annotations", "value": "true"},
            {"label": "without Annotations", "value": "false"},
        ]

    elif column == "prediction":
        return [
            {"label": "with Predictions", "value": "true"},
            {"label": "without Predictions", "value": "false"},
        ]

    else:
        return []
