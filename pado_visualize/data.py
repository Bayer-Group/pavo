"""pado_visualize.data provides access to pado datasets"""
from __future__ import annotations

from enum import Enum
from enum import auto
from functools import cached_property
from functools import wraps
from typing import Callable
from typing import NoReturn
from typing import Optional
from typing import Sequence

from flask import Flask
from flask import current_app

from pado import PadoDataset
from pado.annotations import AnnotationProvider
from pado.images import ImageId
from pado.images import ImageProvider
from pado.io.files import urlpathlike_to_fsspec
from pado.metadata import MetadataProvider

__all__ = [
    "dataset",
    "DatasetNotReadyException",
    "DatasetProxy",  # only used for typing...
    "DatasetState",
    "initialize_dataset",
]


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

    @classmethod
    def new_for_worker_access(cls):
        worker_ds = cls()
        worker_ds.init_app(current_app)
        # clear the fsspec instances
        of = urlpathlike_to_fsspec(worker_ds.urlpath)
        type(of.fs).clear_instance_cache()
        return worker_ds

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

    @cached_property
    def index(self) -> Sequence[ImageId]:
        if self.state != DatasetState.READY:
            raise DatasetNotReadyException(self.state)
        return list(self._ds.index)

    @cached_property
    def metadata(self) -> MetadataProvider:
        if self.state != DatasetState.READY:
            raise DatasetNotReadyException(self.state)
        return self._ds.metadata

    @cached_property
    def images(self) -> ImageProvider:
        if self.state != DatasetState.READY:
            raise DatasetNotReadyException(self.state)
        return self._ds.images

    @cached_property
    def annotations(self) -> AnnotationProvider:
        if self.state != DatasetState.READY:
            raise DatasetNotReadyException(self.state)
        return self._ds.annotations


# interface used throughout the app
dataset = DatasetProxy()


def initialize_dataset(app: Flask) -> DatasetProxy:
    """prepare the dataset"""
    global dataset
    dataset.init_app(app)
    assert not hasattr(app, 'dataset')
    app.dataset = dataset
    return dataset