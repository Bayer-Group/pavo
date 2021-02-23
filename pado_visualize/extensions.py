import hashlib
from functools import wraps

from itsdangerous import base64_decode, base64_encode
from flask import url_for
from pado.images import ImageId
from werkzeug.routing import BaseConverter, ValidationError

from pado_visualize._version import version as _pado_visualize_version


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
        image_id_str = ImageId(value).to_str()
        return base64_encode(image_id_str.encode()).decode()


_version_hash = hashlib.sha256(_pado_visualize_version.encode()).hexdigest()[:8]


@wraps(url_for)
def url_for_versioned(endpoint, **values):
    assert 'v' not in values
    values['v'] = _version_hash
    return url_for(endpoint, **values)
