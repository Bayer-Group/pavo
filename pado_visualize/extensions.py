from itsdangerous import base64_decode, base64_encode
from pado.images import ImageId
from werkzeug.routing import BaseConverter, ValidationError


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
