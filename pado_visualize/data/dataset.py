import json
import shelve
import warnings
from functools import lru_cache, wraps
from pathlib import Path
from typing import Optional, Dict, Literal, overload, List, Tuple

import pandas as pd
from flask import abort
from pado.dataset import PadoDataset
from pado.metadata import PadoReserved, PadoColumn

__all__ = ["init_dataset", "get_dataset", "get_image_map", "get_metadata"]

# data storage
dataset: Optional[PadoDataset] = None
image_map: Optional[Dict[str, Optional[Path]]] = None

# cache_sizes
LRU_CACHE_MAX_SIZE = 16  # these could be split up, but will do for now


def init_dataset(
    dataset_path: Path,
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
            warnings.warn("persist=True requested but cache_file is None")
        persist = False

    # normalize path
    dataset_path = Path(dataset_path).expanduser().absolute().resolve()

    def load_dataset(path):
        # there's no need to set this outside of init_dataset
        try:
            ds = PadoDataset(path, mode="r")
        except FileNotFoundError:
            return None, None
        # build image_id:idx map
        im = {img.id_str: img.local_path for img in ds.images}
        return ds, im

    if not persist:
        dataset, image_map = load_dataset(dataset_path)

    else:
        with shelve.open(str(cache_file)) as store:
            key = str(dataset_path)
            if key not in store or ignore_cache:
                print("loading dataset from disk...", end=" ", flush=True)
                dataset, image_map = store[key] = load_dataset(dataset_path)
            else:
                print("loading dataset from cache...", end=" ", flush=True)
                dataset, image_map = store[key]
    print("OK")


def get_dataset(abort_if_none: bool = True) -> Optional[PadoDataset]:
    global dataset
    if abort_if_none and dataset is None:
        return abort(500, "missing dataset")
    return dataset


def _filter_dict_cache(func):
    """a cache decorator for the get_metadata function"""

    def to_items(f_dict):
        return tuple((k, tuple(sorted(v))) for k, v in sorted(f_dict.items()))

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


@_filter_dict_cache
def get_metadata(
    filter_dict: Optional[Dict[str, List[str]]] = None,
) -> Optional[pd.DataFrame]:
    """return the optionally filtered metadata DataFrame"""
    ds = get_dataset(abort_if_none=False)
    if ds is None:
        return None

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
            return ds.metadata.query(query)
    return ds.metadata


def get_image_map(abort_if_none: bool = True) -> Optional[Dict[str, Optional[Path]]]:
    global image_map
    if abort_if_none and image_map is None:
        return abort(500, "missing image map")
    return image_map


@lru_cache(maxsize=LRU_CACHE_MAX_SIZE)
def get_dataset_column_values(column) -> List[dict]:
    """get the column selections for the subset"""

    # noinspection PyTypeChecker
    ds = get_dataset(abort_if_none=False)
    if ds is None:
        return []

    if column in {
        PadoReserved.DATA_SOURCE_ID,
        PadoColumn.STUDY,
        PadoColumn.ORGAN,
        PadoColumn.FINDING,
    }:
        return [
            {"label": x, "value": x}
            for x in ds.metadata.loc[:, [column]].drop_duplicates()[column].values if isinstance(x, str) and x.strip()
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
