"""
Responsive image pipeline.

Every uploaded image gets resized WebP (and AVIF, when Pillow supports it)
variants stored next to the original under `<dir>/variants/`. Variant names
are cached on the model in a JSONField, so templates never touch the disk.
"""
import logging
import uuid
from io import BytesIO
from pathlib import PurePosixPath

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.utils.deconstruct import deconstructible
from django.utils.text import slugify
from PIL import Image, ImageOps, features

logger = logging.getLogger("maanlab")

AVIF_SUPPORTED = features.check("avif")


@deconstructible
class UploadTo:
    """upload_to callable: stores files as <folder>/<slug>-<uuid>.<ext> (safe, unguessable names)."""

    def __init__(self, folder: str):
        self.folder = folder

    def __call__(self, instance, filename: str) -> str:
        path = PurePosixPath(filename)
        stem = slugify(path.stem)[:40] or "file"
        return f"{self.folder}/{stem}-{uuid.uuid4().hex[:10]}{path.suffix.lower()}"

    def __eq__(self, other):
        return isinstance(other, UploadTo) and other.folder == self.folder


def upload_to(folder: str) -> UploadTo:
    return UploadTo(folder)


def _target_widths(original_width: int) -> list[int]:
    widths = [w for w in settings.IMAGE_VARIANT_WIDTHS if w < original_width]
    top = min(original_width, max(settings.IMAGE_VARIANT_WIDTHS))
    if top not in widths:
        widths.append(top)
    return sorted(set(widths))


def generate_variants(field_file) -> dict:
    storage = field_file.storage
    name = field_file.name
    with storage.open(name, "rb") as fh:
        image = Image.open(fh)
        image = ImageOps.exif_transpose(image)
        image.load()

    width, height = image.size
    has_alpha = image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info)
    image = image.convert("RGBA" if has_alpha else "RGB")

    source = PurePosixPath(name)
    folder = source.parent / "variants"
    result = {"source": name, "width": width, "height": height, "alpha": has_alpha, "webp": [], "avif": []}

    for target in _target_widths(width):
        resized = image if target == width else image.resize(
            (target, max(1, round(height * target / width))), Image.Resampling.LANCZOS
        )
        formats = [("webp", {"quality": 80, "method": 5})]
        if AVIF_SUPPORTED and target <= settings.IMAGE_AVIF_MAX_WIDTH:
            formats.append(("avif", {"quality": 55, "speed": 8}))
        for fmt, options in formats:
            buffer = BytesIO()
            resized.save(buffer, format=fmt.upper(), **options)
            variant_name = str(folder / f"{source.stem}-{target}.{fmt}")
            if storage.exists(variant_name):
                storage.delete(variant_name)
            saved = storage.save(variant_name, ContentFile(buffer.getvalue()))
            result[fmt].append([target, saved])
    return result


def delete_variants(storage, variants: dict) -> None:
    for fmt in ("webp", "avif"):
        for _width, name in variants.get(fmt, []):
            try:
                if storage.exists(name):
                    storage.delete(name)
            except OSError:
                logger.warning("Could not delete image variant %s", name)


class ResponsiveImagesMixin(models.Model):
    """Model mixin: keeps `media_variants` in sync with the listed image fields."""

    RESPONSIVE_IMAGE_FIELDS: tuple[str, ...] = ()

    media_variants = models.JSONField(default=dict, blank=True, editable=False)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.sync_image_variants()

    def sync_image_variants(self, force: bool = False) -> None:
        variants = dict(self.media_variants or {})
        changed = False
        for field_name in self.RESPONSIVE_IMAGE_FIELDS:
            field_file = getattr(self, field_name)
            current = variants.get(field_name)
            if field_file and field_file.name:
                if force or not current or current.get("source") != field_file.name:
                    if current:
                        delete_variants(field_file.storage, current)
                    try:
                        variants[field_name] = generate_variants(field_file)
                        changed = True
                    except Exception:  # noqa: BLE001 — never break a save over thumbnails
                        logger.exception("Could not build variants for %s", field_file.name)
            elif current:
                delete_variants(self._meta.get_field(field_name).storage, current)
                variants.pop(field_name, None)
                changed = True
        if changed:
            type(self).objects.filter(pk=self.pk).update(media_variants=variants)
            self.media_variants = variants

    def variants_for(self, field_name: str) -> dict:
        return (self.media_variants or {}).get(field_name) or {}
