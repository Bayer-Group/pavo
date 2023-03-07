from __future__ import annotations

from typing import Any
from typing import Dict
from typing import Literal
from typing import Tuple
from typing import Union

from flask import Response
from typing_extensions import NotRequired
from typing_extensions import TypeAlias
from typing_extensions import TypedDict

EndpointResponse: TypeAlias = Union[
    str,
    Tuple[str, int],
    Tuple[str, int, Dict[str, str]],
    Response,
    Tuple[Response, int],
    Dict[str, Any],
]


class ConfigMetadataExtraColumn(TypedDict):
    """config dict for extra columns of metadata"""

    name: str
    type: Literal["categorical", "numerical"]
    label: str
    width: NotRequired[int]
