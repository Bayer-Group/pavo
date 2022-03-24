"""pado_visualize.data provides access to pado datasets"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from datetime import timezone
from enum import Enum
from enum import auto
from functools import wraps
from typing import Any
from typing import Callable
from typing import NoReturn
from typing import Optional
from typing import Sequence

import geopandas as gpd
import pandas as pd
from flask import Flask
from fsspec.implementations.cached import SimpleCacheFileSystem
from pado import PadoDataset
from pado.annotations import AnnotationProvider
from pado.images import ImageId
from pado.images import ImageProvider
from pado.images.providers import LocallyCachedImageProvider
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
        self._modified_file = os.path.join(
            tempfile.gettempdir(), ".pado_visualize.timestamp"
        )
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

        # NOTE: currently the returned dataframe contains the following columns:
        OUTPUT_COLUMNS = [
            "image_id",
            "classification",
            "annotation_area",
            "annotation_count",
            "annotator_type",
            "annotator_name",
            "compound_name",
            "organ",
            "species",
            "annotation",
        ]

        def _aggreate(x: pd.Series) -> pd.Series:
            """treat strings differently to integers/floats when aggregating"""
            if isinstance(x[0], int):
                return x.mean()
            elif isinstance(x[0], float):
                return x.mean()
            else:
                # FIXME this is required to aggregate a group but it is assuming that the entire group has the
                # same value in this non int/float column. This is actually not true!
                return x[0]

        def _fill_nan_by_column_type(x: pd.Series) -> pd.Series:
            """fill nans in joined table depending on the name of the column"""
            if "area" in x.name or "count" in x.name:
                return x
            elif "annotator" in x.name:
                return x.fillna("none")
            else:
                # FIXME this will probably cause bugs. When you concatenate and there are NaNs pandas will
                # automatically upcast the entire column to float. So the string columns in this
                # joined database have a float type. To avoid an extremely rigid solution handling each
                # by its name, I resorted to finding the first unique item in the group and assuming that
                # it is a string.
                if x.dropna().shape[0] > 0:
                    return x.fillna(str(x.dropna().unique()[0]))
                else:
                    return x.fillna("unknown")

        adf = self._ds.annotations.df.copy()
        mdf = self._ds.metadata.df.copy()

        pdf = self._ds.predictions.images.df.copy()
        pdf["annotator_type"] = "model"

        def _model_name(x):
            try:
                dct = json.loads(x)
            except json.JSONDecodeError:
                return None
            else:
                for key in ["annotator", "model"]:
                    if key in dct:
                        return dct[key]
                return "-"

        pdf["annotator_name"] = pdf["extra_metadata"].apply(_model_name)

        def _classification(x):
            try:
                dct = json.loads(x)
            except json.JSONDecodeError:
                return None
            else:
                if dct.get("model", "").startswith("aig"):
                    return "Mitosis"
                if dct.get("model", None) == "segmentation-model":
                    return "Mitosis"
                if dct.get("annotator", None) == "multiclass_segmentation_model_v0.1":
                    return "MultiClass"
                return "?"

        pdf["classification"] = pdf.extra_metadata.apply(_classification)
        pdf["area"] = 0.0

        pdf = pdf[
            ["image_id", "classification", "area", "annotator_type", "annotator_name"]
        ]

        # get area of annotations
        if "area" not in adf.columns:
            gs = gpd.GeoSeries.from_wkt(adf["geometry"])
            geo_adf = gpd.GeoDataFrame(adf, geometry=gs)
            adf["area"] = geo_adf.geometry.area

        # get the relevant columns of adf
        adf["annotator_type"] = adf["annotator"].apply(lambda x: x["type"])
        adf["annotator_name"] = adf["annotator"].apply(lambda x: x["name"])
        adf = adf[
            ["image_id", "classification", "area", "annotator_type", "annotator_name"]
        ]

        adf = pd.concat([adf, pdf])

        # get the set of shared rows for annotations and metadata
        common_index = mdf.index.intersection(adf.index)
        if common_index.empty:
            return pd.DataFrame(columns=OUTPUT_COLUMNS)
        else:
            adf = adf.loc[common_index]
            mdf = mdf.loc[common_index]

        # prepare annotations df for joining
        grouped_adf_area = adf.groupby(["image_id", "classification"])["area"]
        grouped_adf_other = adf.drop("area", axis=1).groupby(
            ["image_id", "classification"]
        )
        adf = pd.concat(
            [
                grouped_adf_other.aggregate(_aggreate),
                grouped_adf_area.agg(["count", "sum"]).rename(
                    columns={"count": "annotation_count", "sum": "annotation_area"}
                ),
            ],
            axis=1,
            sort=False,
        )
        # adf = adf.groupby(['image_id', 'classification']).aggregate(_aggreate)

        # prepare metadata df for joining
        mdf = mdf[["compound_name", "organ", "species", "finding_type"]]
        mdf["index"] = mdf.index
        mdf.rename(columns={"finding_type": "classification"}, inplace=True)
        mdf = mdf.groupby(["index", "classification"]).aggregate(_aggreate)

        # join annotations and metadata (the multi-index was neccesary to perform this join)
        table = pd.concat([adf, mdf], axis=1, sort=False)
        table.index.names = ["image_id", "classification"]

        # add some final information and remove nan values
        table["annotation"] = ~table["annotation_area"].isna()
        table = table.groupby(table.index.get_level_values(0)).transform(
            _fill_nan_by_column_type
        )
        table = table.reset_index()

        assert table.columns.sort_values().to_list() == sorted(
            OUTPUT_COLUMNS
        ), f"expected {sorted(OUTPUT_COLUMNS)!r} got {table.columns.sort_values().to_list()!r}"
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
