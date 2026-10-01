"""Upload validators. Uploads are admin-only, but we still validate type and size."""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _

VIDEO_EXTENSIONS = ["mp4", "webm"]
IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "webp", "avif"]

validate_video_extension = FileExtensionValidator(allowed_extensions=VIDEO_EXTENSIONS)
validate_image_extension = FileExtensionValidator(allowed_extensions=IMAGE_EXTENSIONS)


def _max_size(limit_mb: int, label):
    def validator(file):
        if file and getattr(file, "size", 0) > limit_mb * 1024 * 1024:
            raise ValidationError(
                _("%(label)s must be smaller than %(limit)s MB."),
                params={"label": label, "limit": limit_mb},
            )

    return validator


def validate_video_size(file):
    return _max_size(settings.MAX_VIDEO_UPLOAD_MB, _("Video"))(file)


def validate_image_size(file):
    return _max_size(settings.MAX_IMAGE_UPLOAD_MB, _("Image"))(file)


VIDEO_VALIDATORS = [validate_video_extension, validate_video_size]
IMAGE_VALIDATORS = [validate_image_extension, validate_image_size]
