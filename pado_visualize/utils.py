"""some pado_visualize utility objects"""
from __future__ import annotations

import hashlib
from functools import wraps
from typing import Any
from typing import Callable
from typing import Type
from typing import TypeVar
from typing import List
from typing import Union

from flask import url_for
from itsdangerous import base64_decode
from itsdangerous import base64_encode
from werkzeug.routing import BaseConverter
from werkzeug.routing import ValidationError

from pado.images import ImageId
from pado_visualize._version import version as _pado_visualize_version

_T = TypeVar("_T")


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


_version_hash = hashlib.sha256(_pado_visualize_version.encode()).hexdigest()[:8]


@wraps(url_for)
def url_for_versioned(endpoint, **values):
    """use in templates to add a ?v=hash to urls"""
    assert 'v' not in values
    values['v'] = _version_hash
    return url_for(endpoint, **values)


# --- request types ---

def ranged_type(
    cls: Type[_T],
    gt: _T = None, ge: _T = None,
    lt: _T = None, le: _T = None,
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

def check_numeric_list(l: Union[list, None]) -> List[Any]:
    # TODO is there a better way to handle type conversions when the url parameters are always passed as strings from the frontend?
    if l is None:
        return None

    for idx, val in enumerate(l):
        if val.isnumeric() and val[0] != '0':
            l[idx] = int(val)
    return l
