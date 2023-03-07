"""pavo.data provides access to pado datasets"""
from __future__ import annotations

import json
import os
import tempfile
import warnings
from datetime import datetime
from datetime import timezone
from enum import Enum
from enum import auto
from functools import wraps
from operator import itemgetter
from typing import Any
from typing import Callable
from typing import Generic
from typing import NoReturn
from typing import Optional
from typing import Sequence
from typing import TypeVar

import pandas as pd
from flask import Flask
from fsspec.implementations.cached import SimpleCacheFileSystem
from itsdangerous import base64_encode
from pado import PadoDataset
from pado.annotations import AnnotationProvider
from pado.images import ImageId
from pado.images import ImageProvider
from pado.images.providers import LocallyCachedImageProvider
from pado.io.paths import search_dataset
from pado.metadata import MetadataProvider
from pado.predictions.proxy import PredictionProxy
from pandas import DataFrame

from pavo._types import ConfigMetadataExtraColumn

__all__ = [
    "dataset",
    "DatasetNotReadyException",
    "DatasetProxy",  # only used for typing...
    "DatasetState",
    "initialize_dataset",
]

RT = TypeVar("RT")


# noinspection PyPep8Naming
class lockless_cached_property(Generic[RT]):
    # https://bugs.python.org/issue43468
    def __init__(self, func: Callable[..., RT]) -> None:
        self.func = func
        self.__doc__ = func.__doc__

    def __get__(self, instance: object, cls: type | None = None) -> RT:
        if instance is None:
            return self  # type: ignore
        val = instance.__dict__[self.func.__name__] = self.func(instance)
        return val


def _parse_extra_columns(value: Any) -> list[ConfigMetadataExtraColumn]:
    """ensure config value is ok"""
    if not isinstance(value, list):
        raise TypeError(
            f"requires list[ConfigMetadataExtraColumn], got type: {type(value).__name__!r}"
        )
    out = []
    for idx, v in enumerate(value):
        name = v["name"]
        label = v["label"]
        type_ = v["type"]
        width = v.get("width", 160)
        if not isinstance(name, str):
            raise TypeError(f"extra_column[{idx}] {name=!r} is not of type str")
        if not isinstance(label, str):
            raise TypeError(f"extra_column[{idx}] {label=!r} is not of type str")
        if type_ not in {"categorical", "numerical"}:
            raise TypeError(
                f"extra_column[{idx}] {type_=!r} must be 'categorical' or 'numerical'"
            )
        if width and not isinstance(width, int):
            raise TypeError(f"extra_column[{idx}] {width=!r} is not of type int")
        out.append(
            ConfigMetadataExtraColumn(
                name=name,
                type=type_,
                label=label,
                width=width,
            )
        )
    return out


# noinspection PyMethodMayBeStatic
class _Normalize:
    """normization of metadata"""

    def column_names_inplace(self, mdf: DataFrame) -> None:
        mdf.rename(
            columns={
                "finding_type": "classification",
            },
            inplace=True,
        )

    def annotator_name(self, x: str) -> str:
        """take care of legacy names"""
        if x.lower().startswith("tg"):
            return f"TG-{x[2:].title()}"
        elif x.startswith("ai"):
            return f"AI{x[2:]}"
        elif len(x) <= 2:
            return x.upper()
        else:
            return x

    def model_name(self, x: dict) -> str:
        """construct a compatible model name"""
        v = x.get("iteration", "0.0.0")
        m = x.get("model", "unknown")
        if v == "v0":
            return m
        else:
            return f"{m}-{v}"


# noinspection PyMethodMayBeStatic
class _Hotfixes:
    """collection of hot fixes for metadata"""

    def load_tissue_area(self, ds: PadoDataset) -> pd.Series:
        """load tissue area from precomputed df"""
        from geopandas import GeoSeries

        try:
            (of,) = search_dataset(ds, "precomputed.tissue.parquet")
            with of as f:
                _t = pd.read_parquet(f)
                tissue = GeoSeries.from_wkb(_t["tissue"])
            return tissue.area.groupby(tissue.index).sum()
        except BaseException:
            index = ds.index
            data = []
            for iid in index:
                dims = ds.images[iid].dimensions
                data.append(dims.x * dims.y)
            return pd.Series(data, index=list(map(str, index)))

    def ensure_area_column(self, df: DataFrame) -> None:
        """ensure the area column is available in df"""
        from geopandas import GeoDataFrame
        from geopandas import GeoSeries

        if "area" not in df.columns:
            gs = GeoSeries.from_wkt(df["geometry"])
            geo_adf = GeoDataFrame(df, geometry=gs)
            df["area"] = geo_adf.geometry.area


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

    def __init__(self) -> None:
        """default instantiation in not configured state"""
        self.urlpath = None
        self.state = DatasetState.NOT_CONFIGURED
        self._ds: Optional[PadoDataset] = None
        self._cache_path = None
        self._metadata_extra_column_mode: str | None = None
        self._metadata_extra_columns: list[ConfigMetadataExtraColumn] | None = None
        self._modified_file = os.path.join(tempfile.gettempdir(), ".pavo.timestamp")
        self._modified_time: datetime | None = None

    def init_app(self, app: Flask) -> None:
        """initialize the dataset proxy with the Flask app instance"""
        urlpaths = app.config.get("DATASET_PATHS", [])
        assert len(urlpaths) <= 1, "todo: support for multiple datasets"
        self._cache_path = app.config.get("CACHE_IMAGES_PATH", None)

        self._metadata_extra_column_mode = app.config.get("METADATA_EXTRA_COLUMN_MODE")
        self._metadata_extra_columns = _parse_extra_columns(
            app.config.get("METADATA_EXTRA_COLUMNS", [])
        )

        self.urlpath = urlpaths[0] if urlpaths else None
        if self.urlpath:
            self.trigger_refresh()
            self._ds = PadoDataset(self.urlpath, mode="r")
            self.state = DatasetState.READY

    def requires_state(
        self,
        state: DatasetState,
        failure: Callable[..., NoReturn],
        *args: Any,
        **kwargs: Any,
    ) -> Callable:
        """use as a decorator: calls failure in case of wrong state"""
        if not isinstance(state, DatasetState):
            raise ValueError("requires_state can't be used without arguments")

        def decorator(fn: Callable) -> Callable:
            @wraps(fn)
            def wrapper(*fn_args: Any, **fn_kwargs: Any) -> Any:
                if self.state != state:
                    failure(*args, **kwargs)
                    raise AssertionError(
                        f"callable failure={failure.__name__!r} must raise an exception"
                    )
                else:
                    return fn(*fn_args, **fn_kwargs)

            return wrapper

        return decorator

    def get_ds(self) -> PadoDataset:
        if self.state != DatasetState.READY:
            raise DatasetNotReadyException(self.state)
        self._check_refresh()
        if self._ds is None:
            raise RuntimeError("dataset is None")
        return self._ds

    @lockless_cached_property
    def index(self) -> Sequence[ImageId]:
        return list(self.get_ds().index)

    @lockless_cached_property
    def metadata(self) -> MetadataProvider:
        return self.get_ds().metadata

    @lockless_cached_property
    def images(self) -> ImageProvider:
        ds = self.get_ds()
        if self._cache_path is None:
            return ds.images
        else:
            return LocallyCachedImageProvider(
                ds.images,
                cache_cls=SimpleCacheFileSystem,
                cache_storage=self._cache_path,
            )

    @lockless_cached_property
    def annotations(self) -> AnnotationProvider:
        return self.get_ds().annotations

    @lockless_cached_property
    def predictions(self) -> PredictionProxy:
        return self.get_ds().predictions

    def describe(self) -> dict[str, Any]:
        ds = self.get_ds()
        try:
            description = self.__dict__["_describe"]
        except KeyError:
            description = self.__dict__["_describe"] = ds.describe(output_format="json")
        return description

    def get_tabular_records_df(self) -> pd.DataFrame:
        """tabular representation of the dataset including metadata and annotations

        Each row is either a finding from the metadata provider or from the
        annotations provider. It returns a dataframe of records where each record
        is of the form:
        (ImageId, classification, area, annotator_type, annotator_name,
        compound_name, organ, species)
        """
        ds = self.get_ds()
        try:
            return self.__dict__["_tabular_records_df"]
        except KeyError:
            pass  # cache miss

        OUTPUT_COLUMNS = [
            "image_id",
            "image_url",
            "classification",
            "annotation_type",
            "annotator_type",
            "annotator_name",
            "annotation_area",
            "annotation_count",
            "annotation_metric",
            "annotation_value",
        ]

        xcolumns = []
        for xcol_dct in self._metadata_extra_columns or []:
            xcolumns.append(xcol_dct["name"])

        # === prepare metadata df for joining =================================
        normalize = _Normalize()
        hotfixes = _Hotfixes()

        mdf = ds.metadata.df.copy()
        normalize.column_names_inplace(mdf)
        available_xcolumns = [c for c in xcolumns if c in mdf.columns]

        if set(available_xcolumns) != set(xcolumns):
            if self._metadata_extra_column_mode == "ignore_missing":
                warnings.warn("requested columns are not available in dataframe")
            else:
                raise ValueError()
        OUTPUT_COLUMNS.extend(available_xcolumns)

        mdf = mdf[["classification", *available_xcolumns]]
        mdf = mdf.reset_index(names="image_id")
        mdf["annotator_name"] = normalize.annotator_name(ds.metadata.identifier)
        mdf["annotator_type"] = "dataset"
        mdf["annotation_area"] = None
        mdf["annotation_count"] = None
        mdf["classification"] = mdf["classification"].fillna("None")
        mdf["annotation_type"] = "slide"
        mdf["annotation_metric"] = None
        mdf["annotation_value"] = None

        _xcolumn_map = {
            c: mdf[["image_id", c]].drop_duplicates().set_index("image_id")[c]
            for c in available_xcolumns
        }

        # === prepare the annotation df for joining ===========================
        adf = ds.annotations.df.copy()

        hotfixes.ensure_area_column(adf)

        adf["annotator_type"] = adf["annotator"].apply(lambda x: x["type"])
        adf["annotator_name"] = adf["annotator"].apply(
            lambda x: normalize.annotator_name(x["name"])
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
        for xcol in available_xcolumns:
            adf[xcol] = adf["image_id"].map(_xcolumn_map[xcol])
        adf["annotation_type"] = "contour"

        _tissue = hotfixes.load_tissue_area(ds)
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
        ipdf = ds.predictions.images.df.copy()
        _model_metadata = ipdf["extra_metadata"].apply(json.loads)

        ipdf = ipdf[["image_id"]]
        ipdf["classification"] = _model_metadata.apply(lambda x: x.get("classes"))
        ipdf["annotator_name"] = _model_metadata.apply(normalize.model_name)
        ipdf["annotator_type"] = "model"
        for xcol in available_xcolumns:
            ipdf[xcol] = ipdf["image_id"].map(_xcolumn_map[xcol])

        ipdf["annotation_type"] = "heatmap"  # fixme: segmentation vs others...
        ipdf["annotation_metric"] = "area"  # fixme
        ipdf["annotation_value"] = None
        ipdf["annotation_area"] = None  # provided via MetadataPredictionProvider
        ipdf["annotation_count"] = None  # fixme: calculate

        ipdf = ipdf.explode("classification")
        ipdf = ipdf.loc[ipdf["classification"] != "other", :]
        ipdf["classification"] = ipdf["classification"].str.title()

        # === prepare metadata prediction dataframe for joining ===============
        mpdf = ds.predictions.metadata.df.copy()
        _model_metadata = mpdf["model_extra_json"].apply(json.loads)
        _row_data = mpdf["row_json"].apply(json.loads)
        mpdf = mpdf[["image_id"]]
        mpdf["classification"] = _row_data.apply(
            itemgetter("classification")
        ).str.title()
        mpdf["annotator_name"] = _model_metadata.apply(normalize.model_name)
        mpdf["annotator_type"] = "model"
        for xcol in available_xcolumns:
            mpdf[xcol] = mpdf["image_id"].map(_xcolumn_map[xcol])

        _metric = _row_data.apply(itemgetter("metric"))
        _score = _row_data.apply(itemgetter("value"))
        _mask = mpdf["annotator_name"].str.startswith("AIg") | (
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
                (ipdf["annotator_name"].str.startswith("AIg"))
                | (ipdf["annotator_name"] == "MultiClassSegmentation-v0.1")
            )
        ]

        # === join and validate ===============================================
        table = pd.concat([mdf, adf, ipdf, mpdf], axis=0)
        table["image_url"] = table["image_id"].apply(
            lambda x: base64_encode(x.encode()).decode()
        )

        if set(table.columns) != set(OUTPUT_COLUMNS):
            raise RuntimeError(f"expected {OUTPUT_COLUMNS!r} got {table.columns!r}")

        # === cache and return ================================================
        tabular_records_df = self.__dict__["_tabular_records_df"] = table
        return tabular_records_df

    def get_tabular_records_json(self) -> str:
        """return tabular records df as json"""
        recs = self.get_tabular_records_df().to_json(orient="records")
        recs_json = self.__dict__["_tabular_records_json"] = recs
        return recs_json

    # --- refreshing ---

    def trigger_refresh(self) -> datetime:
        with open(self._modified_file, "a"):
            pass
        ts = os.stat(self._modified_file).st_mtime
        return datetime.utcfromtimestamp(ts).replace(tzinfo=timezone.utc)

    def _check_refresh(self) -> None:
        ts = os.stat(self._modified_file).st_mtime
        dt = datetime.utcfromtimestamp(ts).replace(tzinfo=timezone.utc)
        if self._modified_time is None or dt > self._modified_time:
            self._modified_time = max([self._last_change(), dt])
            self._ds = PadoDataset(self.urlpath, mode="r")
            self._clear_caches()

    def _last_change(self) -> datetime:
        ds = self._ds
        if ds is None:
            return datetime.fromtimestamp(0, tz=timezone.utc)
        # noinspection PyProtectedMember
        fs, root = ds._fs, ds._root
        try:
            return max(
                x["LastModified"]
                for x in fs.ls(root, detail=True, refresh=True)
                if "LastModified" in x
            )
        except ValueError:
            return datetime.fromtimestamp(0, tz=timezone.utc)

    def _clear_caches(self) -> None:
        caches = [
            "index",
            "images",
            "metadata",
            "annotations",
            "predictions",
            "_describe",
            "_tabular_records_df",
            "_tabular_records_json",
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
    app.dataset = dataset  # type: ignore
    return dataset
