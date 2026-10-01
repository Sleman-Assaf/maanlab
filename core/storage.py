from whitenoise.storage import CompressedManifestStaticFilesStorage


class MaanStaticStorage(CompressedManifestStaticFilesStorage):
    """Hashed + compressed static files; also rewrites ES-module import paths."""

    support_js_module_import_aggregation = True
    manifest_strict = False
