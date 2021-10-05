"""pado_visualize.data provides access to pado datasets"""
from __future__ import annotations

from enum import Enum
from enum import auto
from functools import wraps
from typing import Callable
from typing import NoReturn
from typing import Optional
from typing import Sequence

from flask import Flask

from pado import PadoDataset
from pado.annotations import AnnotationProvider
from pado.images import ImageId
from pado.images import ImageProvider
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

    def describe(self, output_format: str) -> str:
        if self.state != DatasetState.READY:
            raise DatasetNotReadyException(self.state)
        return self._ds.describe(output_format)


# interface used throughout the app
dataset = DatasetProxy()


def initialize_dataset(app: Flask) -> DatasetProxy:
    """prepare the dataset"""
    global dataset
    dataset.init_app(app)
    assert not hasattr(app, 'dataset')
    app.dataset = dataset
    return dataset
