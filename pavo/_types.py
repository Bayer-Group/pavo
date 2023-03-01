from __future__ import annotations

from typing import Any
from typing import Dict
from typing import Tuple
from typing import Union

from flask import Response
from typing_extensions import TypeAlias

EndpointResponse: TypeAlias = Union[
    str,
    Tuple[str, int],
    Tuple[str, int, Dict[str, str]],
    Response,
    Tuple[Response, int],
    Dict[str, Any],
]
