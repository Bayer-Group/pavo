"""pavo.data provides access to pado datasets"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from datetime import timezone
from enum import Enum
from enum import auto
from functools import wraps
from operator import itemgetter
from typing import Any
from typing import Callable
from typing import NoReturn
from typing import Optional
from typing import Sequence

import pandas as pd
from flask import Flask
from fsspec.implementations.cached import SimpleCacheFileSystem
from itsdangerous import base64_encode
from pado import PadoDataset
from pado.annotations import AnnotationProvider
from pado.images import ImageId
from pado.images import ImageProvider
from pado.images.providers import LocallyCachedImageProvider
from pado.io.files import fsopen
from pado.metadata import MetadataProvider
from pado.predictions.proxy import PredictionProxy

__all__ = [
    "dataset",
    "DatasetNotReadyException",
    "DatasetProxy",  # only used for typing...
    "DatasetState",
    "initialize_dataset",
]


# noinspection PyPep8Naming
class lockless_cached_property:
    # https://bugs.python.org/issue43468
    def __init__(self, func):
        self.func = func
        self.__doc__ = func.__doc__

    def __get__(self, instance, cls=None):
        if instance is None:
            return self
        val = instance.__dict__[self.func.__name__] = self.func(instance)
        return val


class DatasetState(Enum):
    """indicates current state of the loaded proxy"""

    NOT_CONFIGURED = auto()
    READY = auto()


class DatasetNotReadyException(Exception):
    def __init__(self, state: DatasetState):
        super().__init__(state)
        self.state: DatasetState = state


class DatasetProxy:
    """a proxy for accessing the pado dataset"""

    urlpath: Optional[str]
    state: DatasetState

    def __init__(self):
        """default instantiation in not configured state"""
        self.urlpath = None
        self.state = DatasetState.NOT_CONFIGURED
        self._ds: Optional[PadoDataset] = None
        self._cache_path = None
        self._modified_file = os.path.join(tempfile.gettempdir(), ".pavo.timestamp")
        self._modified_time = None

    def init_app(self, app: Flask) -> None:
        """initialize the dataset proxy with the Flask app instance"""
        urlpaths = app.config.get("DATASET_PATHS", [])
        assert len(urlpaths) <= 1, "todo: support for multiple datasets"
        self._cache_path = app.config.get("CACHE_IMAGES_PATH", None)

        self.urlpath = urlpaths[0] if urlpaths else None
        if self.urlpath:
            self.trigger_refresh()
            self._ds = PadoDataset(self.urlpath, mode="r")
            self.state = DatasetState.READY

    def requires_state(
        self,
        state: DatasetState,
        failure: Callable[[...], NoReturn],
        *args,
        **kwargs,
    ):
        """use as a decorator: calls failure in case of wrong state"""
        if not isinstance(state, DatasetState):
            raise ValueError("requires_state can't be used without arguments")

        def decorator(fn):
            @wraps(fn)
            def wrapper(*fn_args, **fn_kwargs):
                if self.state != state:
                    failure(*args, **kwargs)
                    raise AssertionError(
                        f"callable failure={failure.__name__!r} must raise an exception"
                    )
                else:
                    return fn(*fn_args, **fn_kwargs)

            return wrapper

        return decorator

    # type annotations until https://youtrack.jetbrains.com/issue/PY-47698 is fixed
    index: Sequence[ImageId]
    metadata: MetadataProvider
    images: ImageProvider
    annotations: AnnotationProvider
    predictions: PredictionProxy

    @lockless_cached_property
    def index(self) -> Sequence[ImageId]:
        if self.state != DatasetState.READY:
            raise DatasetNotReadyException(self.state)
        self._check_refresh()
        return list(self._ds.index)

    @lockless_cached_property
    def metadata(self) -> MetadataProvider:
        if self.state != DatasetState.READY:
            raise DatasetNotReadyException(self.state)
        self._check_refresh()
        return self._ds.metadata

    @lockless_cached_property
    def images(self) -> ImageProvider:
        if self.state != DatasetState.READY:
            raise DatasetNotReadyException(self.state)
        self._check_refresh()
        if self._cache_path is None:
            return self._ds.images
        else:
            return LocallyCachedImageProvider(
                self._ds.images,
                cache_cls=SimpleCacheFileSystem,
                cache_storage=self._cache_path,
            )

    @lockless_cached_property
    def annotations(self) -> AnnotationProvider:
        if self.state != DatasetState.READY:
            raise DatasetNotReadyException(self.state)
        self._check_refresh()
        return self._ds.annotations

    @lockless_cached_property
    def predictions(self) -> PredictionProxy:
        if self.state != DatasetState.READY:
            raise DatasetNotReadyException(self.state)
        self._check_refresh()
        return self._ds.predictions

    def describe(self) -> dict[str, Any]:
        if self.state != DatasetState.READY:
            raise DatasetNotReadyException(self.state)
        self._check_refresh()
        try:
            description = self.__dict__["_describe"]
        except KeyError:
            description = self.__dict__["_describe"] = self._ds.describe(
                output_format="json"
            )
        return description

    def get_tabular_records(self) -> pd.DataFrame:
        """tabular representation of the dataset including metadata and annotations

        Each row is either a finding from the metadata provider or from the
        annotations provider. It returns a dataframe of records where each record
        is of the form:
        (ImageId, classification, area, annotator_type, annotator_name,
        compound_name, organ, species)
        """
        if self.state != DatasetState.READY:
            raise DatasetNotReadyException(self.state)
        self._check_refresh()
        try:
            return self.__dict__["_tabular_records"]
        except KeyError:
            pass  # cache miss

        # === lazy import geopandas when needed ===============================
        from geopandas import GeoDataFrame
        from geopandas import GeoSeries

        # NOTE: currently the returned dataframe contains the following columns:
        OUTPUT_COLUMNS = [
            "image_id",
            "image_url",
            "classification",
            "annotation_type",
            "annotator_type",
            "annotator_name",
            "compound_name",
            "organ",
            "species",
            "annotation_area",
            "annotation_count",
            "annotation_metric",
            "annotation_value",
        ]

        def _special_title(x: str) -> str:
            if x.lower().startswith("tg"):
                return f"TG-{x[2:].title()}"
            if x.startswith("ai"):
                return f"AI{x[2:]}"
            if len(x) <= 2:
                return x.upper()
            return x

        def _model_name(x: dict) -> str:
            v = x["iteration"]
            return x["model"] if v == "v0" else f"{x['model']}-{v}"

        def _recover_area_df() -> pd.Series:
            try:
                fs, get_fspath = self._ds._fs, self._ds._get_fspath
                pth = get_fspath("precomputed.tissue.parquet")
                with fsopen(fs, pth) as f:
                    _t = pd.read_parquet(f)
                    tissue = GeoSeries.from_wkb(_t["tissue"])
                return tissue.area.groupby(tissue.index).sum()
            except BaseException:
                index = self._ds.index
                data = []
                for iid in index:
                    dims = self._ds.images[iid].dimensions
                    data.append(dims.x * dims.y)
                return pd.Series(data, index=list(map(str, index)))

        # === prepare metadata df for joining =================================
        mdf = self._ds.metadata.df.copy()

        mdf = mdf[["finding_type", "compound_name", "species", "organ"]].reset_index()
        mdf.rename(
            columns={
                "index": "image_id",
                "finding_type": "classification",
            },
            inplace=True,
        )
        mdf["annotator_name"] = _special_title(self._ds.metadata.identifier)
        mdf["annotator_type"] = "dataset"
        mdf["annotation_area"] = None
        mdf["annotation_count"] = None
        mdf["classification"] = mdf["classification"].fillna("None")
        mdf["annotation_type"] = "slide"
        mdf["annotation_metric"] = None
        mdf["annotation_value"] = None

        _organ_map = (
            mdf[["image_id", "organ"]].drop_duplicates().set_index("image_id")["organ"]
        )
        _species_map = (
            mdf[["image_id", "species"]]
            .drop_duplicates()
            .set_index("image_id")["species"]
        )
        _compound_map = (
            mdf[["image_id", "compound_name"]]
            .drop_duplicates()
            .set_index("image_id")["compound_name"]
        )

        # === prepare the annotation df for joining ===========================
        adf = self._ds.annotations.df.copy()

        if "area" not in adf.columns:
            gs = GeoSeries.from_wkt(adf["geometry"])
            geo_adf = GeoDataFrame(adf, geometry=gs)
            adf["area"] = geo_adf.geometry.area

        adf["annotator_type"] = adf["annotator"].apply(lambda x: x["type"])
        adf["annotator_name"] = adf["annotator"].apply(
            lambda x: _special_title(x["name"])
        )
        adf = adf[
            ["image_id", "classification", "area", "annotator_type", "annotator_name"]
        ]
        adf = (
            adf.groupby(
                ["image_id", "classification", "annotator_type", "annotator_name"]
            )["area"]
            .agg(["sum", "count"])
            .rename(columns={"sum": "annotation_area", "count": "annotation_count"})
            .reset_index()
        )
        adf["organ"] = adf["image_id"].map(_organ_map)
        adf["species"] = adf["image_id"].map(_species_map)
        adf["compound_name"] = adf["image_id"].map(_compound_map)
        adf["annotation_type"] = "contour"

        _tissue = _recover_area_df()
        _tissue_area = adf["image_id"].map(_tissue)
        adf["annotation_area"] = adf["annotation_area"] / _tissue_area * 100

        count_mask = adf["classification"].str.lower().str.contains("mitosis")
        adf["annotation_metric"] = None
        adf.loc[~count_mask, "annotation_metric"] = "area"
        adf.loc[count_mask, "annotation_area"] = None
        adf.loc[count_mask, "annotation_metric"] = "count"
        adf.loc[~count_mask, "annotation_count"] = None
        adf["annotation_value"] = None

        # === prepare image prediction dataframe for joining ==================
        ipdf = self._ds.predictions.images.df.copy()
        _model_metadata = ipdf["extra_metadata"].apply(json.loads)

        ipdf = ipdf[["image_id"]]
        ipdf["classification"] = _model_metadata.apply(itemgetter("classes"))
        ipdf["annotator_name"] = _model_metadata.apply(_model_name)
        ipdf["annotator_type"] = "model"
        ipdf["organ"] = ipdf["image_id"].map(_organ_map)
        ipdf["species"] = ipdf["image_id"].map(_species_map)
        ipdf["compound_name"] = ipdf["image_id"].map(_compound_map)

        ipdf["annotation_type"] = "heatmap"  # fixme: segmentation vs others...
        ipdf["annotation_metric"] = "area"  # fixme
        ipdf["annotation_value"] = None
        ipdf["annotation_area"] = None  # provided via MetadataPredictionProvider
        ipdf["annotation_count"] = None  # fixme: calculate

        ipdf = ipdf.explode("classification")
        ipdf = ipdf.loc[ipdf["classification"] != "other", :]
        ipdf["classification"] = ipdf["classification"].str.title()

        # === prepare metadata prediction dataframe for joining ===============
        mpdf = self._ds.predictions.metadata.df.copy()
        _model_metadata = mpdf["model_extra_json"].apply(json.loads)
        _row_data = mpdf["row_json"].apply(json.loads)
        mpdf = mpdf[["image_id"]]
        mpdf["classification"] = _row_data.apply(
            itemgetter("classification")
        ).str.title()
        mpdf["annotator_name"] = _model_metadata.apply(_model_name)
        mpdf["annotator_type"] = "model"
        mpdf["organ"] = mpdf["image_id"].map(_organ_map)
        mpdf["species"] = mpdf["image_id"].map(_species_map)
        mpdf["compound_name"] = mpdf["image_id"].map(_compound_map)

        _metric = _row_data.apply(itemgetter("metric"))
        _score = _row_data.apply(itemgetter("value"))
        _mask = (mpdf["annotator_name"] == "AIgnostics-v3") | (
            mpdf["annotator_name"] == "MultiClassSegmentation-v0.1"
        )

        mpdf["annotation_type"] = "slide"
        mpdf.loc[_mask, "annotation_type"] = "heatmap"
        mpdf["annotation_area"] = _score * 100
        mpdf.loc[~_mask, "annotation_area"] = None
        mpdf["annotation_count"] = None  # fixme: calculate
        mpdf["annotation_metric"] = _metric
        mpdf.loc[_mask, "annotation_metric"] = "area"
        mpdf["annotation_value"] = _score
        mpdf.loc[_mask, "annotation_value"] = None

        mpdf = mpdf.loc[mpdf["classification"] != "Other", :]

        # === transfer area score for segmentation models =====================
        ipdf = ipdf.loc[
            ~(
                (ipdf["annotator_name"] == "AIgnostics-v3")
                | (ipdf["annotator_name"] == "MultiClassSegmentation-v0.1")
            )
        ]

        # === join and validate ===============================================
        table = pd.concat([mdf, adf, ipdf, mpdf], axis=0)
        table["image_url"] = table["image_id"].apply(
            lambda x: base64_encode(x.encode()).decode()
        )

        assert set(table.columns) == set(
            OUTPUT_COLUMNS
        ), f"expected {OUTPUT_COLUMNS!r} got {table.columns!r}"

        # === cache and return ================================================
        tabular_records = self.__dict__["_tabular_records"] = table
        return tabular_records

    # --- refreshing ---

    def trigger_refresh(self) -> datetime:
        with open(self._modified_file, "a"):
            pass
        ts = os.stat(self._modified_file).st_mtime
        return datetime.utcfromtimestamp(ts).replace(tzinfo=timezone.utc)

    def _check_refresh(self):
        ts = os.stat(self._modified_file).st_mtime
        dt = datetime.utcfromtimestamp(ts).replace(tzinfo=timezone.utc)
        if self._modified_time is None or dt > self._modified_time:
            self._modified_time = max([self._last_change(), dt])
            self._ds = PadoDataset(self.urlpath, mode="r")
            self._clear_caches()

    def _last_change(self) -> datetime:
        # noinspection PyProtectedMember
        fs, root = self._ds._fs, self._ds._root
        try:
            return max(
                x["LastModified"]
                for x in fs.ls(root, detail=True, refresh=True)
                if "LastModified" in x
            )
        except ValueError:
            return datetime.fromtimestamp(0, tz=timezone.utc)

    def _clear_caches(self):
        caches = [
            "index",
            "images",
            "metadata",
            "annotations",
            "predictions",
            "_describe",
            "_tabular_records",
        ]
        for key in caches:
            try:
                del self.__dict__[key]
            except KeyError:
                pass


# interface used throughout the app
dataset = DatasetProxy()


def initialize_dataset(app: Flask) -> DatasetProxy:
    """prepare the dataset"""
    global dataset
    dataset.init_app(app)
    assert not hasattr(app, "dataset")
    app.dataset = dataset
    return dataset
