"""some pavo utility objects"""
from __future__ import annotations

import hashlib
import os
import platform
from functools import lru_cache
from functools import wraps
from getpass import getuser
from typing import Any
from typing import Callable
from typing import Type
from typing import TypeVar

from flask import url_for
from itsdangerous import base64_decode
from itsdangerous import base64_encode
from pado import __version__ as _pado_version
from pado._repr import is_mpp_count
from pado._repr import is_number
from pado._repr import number_to_str
from pado.images import ImageId
from tiffslide import __version__ as _tiffslide_version
from werkzeug.routing import BaseConverter
from werkzeug.routing import ValidationError

from pavo._version import version as _pavo_version

_T = TypeVar("_T")

__all__ = [
    "ImageIdConverter",
    "url_for_versioned",
    "ranged_type",
    "int_ge_0",
    "int_ge_1",
    "check_numeric_list",
    "number_to_str",
    "is_number",
    "is_mpp_count",
    "get_instance_name",
    "get_instance_version",
]


# --- endpoint handling ---


class ImageIdConverter(BaseConverter):
    """a converter for image ids from pado"""

    regex = "[^/]+"
    weight = 100

    def to_python(self, value) -> ImageId:
        try:
            image_id_str = base64_decode(value).decode()
            return ImageId.from_str(image_id_str)
        except (ValueError, TypeError):
            raise ValidationError(value)

    def to_url(self, value):
        if isinstance(value, ImageId):
            image_id_str = value.to_str()
        elif isinstance(value, (tuple, list)):
            image_id_str = ImageId.make(value[1:], site=value[0]).to_str()
        elif isinstance(value, str):
            # TODO: check that the ImageId string is valid somehow
            image_id_str = value
        else:
            raise NotImplementedError(f"todo: {type(value).__name__!r} for {value!r}")
        return base64_encode(image_id_str.encode()).decode()


_version_hash = hashlib.sha256(_pavo_version.encode()).hexdigest()[:8]


@wraps(url_for)
def url_for_versioned(endpoint, **values):
    """use in templates to add a ?v=hash to urls"""
    assert "v" not in values
    values["v"] = _version_hash
    return url_for(endpoint, **values)


# --- request types ---


def ranged_type(
    cls: Type[_T],
    gt: _T = None,
    ge: _T = None,
    lt: _T = None,
    le: _T = None,
) -> Callable[[Any], _T]:
    """check if type can be cast to and is in range"""

    def _type(x):
        value = cls(x)  # might raise
        if lt is not None:
            if lt >= value:
                raise ValueError(f"bound: {value!r} < {lt!r}")
        if le is not None:
            if le > value:
                raise ValueError(f"bound: {value!r} <= {le!r}")
        if gt is not None:
            if value <= gt:
                raise ValueError(f"bound: {value!r} > {gt!r}")
        if ge is not None:
            if value < ge:
                raise ValueError(f"bound: {value!r} >= {gt!r}")
        return value

    return _type


int_ge_0 = ranged_type(int, ge=0)
int_ge_1 = ranged_type(int, ge=1)


def check_numeric_list(lst: list | None) -> list | None:
    """converts integer like strings in a list to integers"""
    # todo: check where this is used
    if lst is None:
        return None

    if not isinstance(lst, list):
        raise TypeError(f"expected list or None, got {type(lst).__name__}")

    for idx, value in enumerate(lst):
        if isinstance(value, str) and value.isnumeric() and value[0] != "0":
            lst[idx] = int(value)

    return lst


@lru_cache
def get_instance_name() -> str | None:
    """return a name to identify the pavo instance"""
    name = os.getenv("PAVO_INSTANCE_NAME")
    if name is None:
        from flask import current_app

        if current_app.config.env == "development":
            try:
                name = f"{getuser()!s}@{platform.uname().node!s}"
            except (OSError, KeyError, ValueError):
                pass
    return name or None


@lru_cache
def get_instance_version() -> dict:
    """return pavo instance version information"""
    return {
        "pavo": _pavo_version,
        "pado": _pado_version,
        "tiffslide": _tiffslide_version,
    }
