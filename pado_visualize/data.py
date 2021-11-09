"""pado_visualize.data provides access to pado datasets"""
from __future__ import annotations

from enum import Enum
from enum import auto
from functools import lru_cache, wraps
from typing import Callable
from typing import NoReturn
from typing import Optional
from typing import Sequence
from typing import Mapping

import pandas as pd
import geopandas as gpd

from flask import Flask

from pado import PadoDataset
from pado.annotations import AnnotationProvider
from pado.images import ImageId
from pado.images import ImageProvider
from pado.images.image import Image
from pado.metadata import MetadataProvider

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

    def init_app(self, app: Flask) -> None:
        """initialize the dataset proxy with the Flask app instance"""
        urlpaths = app.config.get("DATASET_PATHS", [])
        assert len(urlpaths) <= 1, "todo: support for multiple datasets"

        self.urlpath = urlpaths[0] if urlpaths else None
        if self.urlpath:
            self._ds = PadoDataset(self.urlpath, mode="r")
            self.state = DatasetState.READY

    def requires_state(self, state: DatasetState, failure: Callable[[...], NoReturn], *args, **kwargs):
        """use as a decorator: calls failure in case of wrong state"""
        if not isinstance(state, DatasetState):
            raise ValueError("requires_state can't be used without arguments")

        def decorator(fn):
            @wraps(fn)
            def wrapper(*fn_args, **fn_kwargs):
                if self.state != state:
                    failure(*args, **kwargs)
                    raise AssertionError(f"callable failure={failure.__name__!r} must raise an exception")
                else:
                    return fn(*fn_args, **fn_kwargs)
            return wrapper
        return decorator

    @lockless_cached_property
    def index(self) -> Sequence[ImageId]:
        if self.state != DatasetState.READY:
            raise DatasetNotReadyException(self.state)
        return list(self._ds.index)

    @lockless_cached_property
    def metadata(self) -> MetadataProvider:
        if self.state != DatasetState.READY:
            raise DatasetNotReadyException(self.state)
        return self._ds.metadata

    @lockless_cached_property
    def images(self) -> ImageProvider:
        if self.state != DatasetState.READY:
            raise DatasetNotReadyException(self.state)
        return self._ds.images

    @lockless_cached_property
    def annotations(self) -> AnnotationProvider:
        if self.state != DatasetState.READY:
            raise DatasetNotReadyException(self.state)
        return self._ds.annotations

    @lru_cache
    def describe(self, output_format: str) -> str:
        if self.state != DatasetState.READY:
            raise DatasetNotReadyException(self.state)
        return self._ds.describe(output_format)

    @lru_cache
    def get_tabular_records(self) -> pd.DataFrame:
        """tabular representation of the dataset including metadata and annotations
        
        Each row is either a finding from the metadata provider or from the 
        annotations provider. It returns a dataframe of records where each record
        is of the form:
        (ImageId, classification, area, annotator_type, annotator_name, 
        compound_name, organ, species)
        """
        # NOTE: currently the returned dataframe contains the following columns:
        OUTPUT_COLUMNS = [
            'image_id',
            'classification',
            'area',
            'annotator_type',
            'annotator_name',
            'compound_name',
            'organ',
            'species',
            'annotation',
        ]

        def _aggreate_annotations(x: pd.Series) -> pd.Series:
            """treat strings differently to intergers/floats when aggregating"""
            if isinstance(x[0], int):
                return x.mean()
            elif isinstance(x[0], float):
                return x.mean()
            else:
                return x[0]
        
        def _fill_nan_by_column_type(x: pd.Series) -> pd.Series:
            """fill nans in joined table depending on the name of the column"""
            if 'area' in x.name:
                return x
            elif 'annotator' in x.name:
                return x.fillna('none')
            elif isinstance(x[0], str):
                return x.fillna(x.dropna().unique()[0])
            else:
                return x

        adf = self._ds.annotations.df.copy()
        mdf = self._ds.metadata.df.copy()

        # get area of annotations
        if 'area' not in adf.columns:
            gs = gpd.GeoSeries.from_wkt(adf['geometry'])
            geo_adf = gpd.GeoDataFrame(adf, geometry=gs)
            adf['area'] = geo_adf.geometry.area

        # get the relevant columns of adf
        adf['annotator_type'] = adf['annotator'].apply(lambda x: x["type"])
        adf['annotator_name'] = adf['annotator'].apply(lambda x: x["name"])
        adf = adf[['classification', 'area', 'annotator_type', 'annotator_name']]

        # get the set of shared rows for annotations and metadata
        common_index = mdf.index.intersection(adf.index)
        if common_index.empty:
            return pd.DataFrame(columns=OUTPUT_COLUMNS)
        else:
            adf = adf.loc[common_index]
            mdf = mdf.loc[common_index]
        
        # prepare annotations df for joining
        adf['image_id'] = adf.index
        adf = adf.groupby(['image_id', 'classification']).aggregate(_aggreate_annotations)

        # prepare metadata df for joining
        mdf = mdf[['compound_name', 'organ', 'species', 'finding_type']]
        mdf['index'] = mdf.index
        mdf.rename(columns={'finding_type': 'classification'}, inplace=True)
        mdf.set_index(['index', 'classification'], inplace=True)

        # join annotations and metadata (the multi-index was neccesary to perform this join)
        table = pd.concat([adf, mdf], axis=1, sort=False)
        table.index.names = ['image_id', 'classification']

        # add some final information and remove nan values
        table['annotation'] = ~table['area'].isna()
        table = table.transform(_fill_nan_by_column_type)
        table = table.reset_index()

        assert all(table.columns == OUTPUT_COLUMNS), f"expected {OUTPUT_COLUMNS!r} got {table.columns!r}"
        return table


# interface used throughout the app
dataset = DatasetProxy()


def initialize_dataset(app: Flask) -> DatasetProxy:
    """prepare the dataset"""
    global dataset
    dataset.init_app(app)
    assert not hasattr(app, 'dataset')
    app.dataset = dataset
    return dataset
