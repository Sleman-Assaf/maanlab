"""
Development-only media view with HTTP Range support.

django.views.static.serve always sends the whole file, which stops Safari from
playing video at all and prevents seeking elsewhere. In production /media/ is
served by the web server or CDN (nginx, S3/CloudFront…), which handle Range natively.
"""
import mimetypes
import re
from pathlib import Path

from django.conf import settings
from django.http import Http404, HttpResponse
from django.utils._os import safe_join
from django.views.static import serve

RANGE_RE = re.compile(r"^bytes=(\d*)-(\d*)$")
CHUNK = 8 * 1024 * 1024  # at most 8 MB per open-ended range response


def serve_media(request, path):
    try:
        full = Path(safe_join(settings.MEDIA_ROOT, path))
    except Exception:  # path traversal attempt
        raise Http404
    match = RANGE_RE.match(request.headers.get("Range", ""))
    if not match or not full.is_file():
        return serve(request, path, document_root=settings.MEDIA_ROOT)

    size = full.stat().st_size
    first, last = match.groups()
    if first:
        start = int(first)
        end = int(last) if last else min(start + CHUNK, size) - 1
    else:  # "bytes=-N": the final N bytes
        start, end = max(size - int(last or 0), 0), size - 1
    end = min(end, size - 1)
    if start >= size or start > end:
        response = HttpResponse(status=416)
        response["Content-Range"] = f"bytes */{size}"
        return response

    with open(full, "rb") as fh:
        fh.seek(start)
        data = fh.read(end - start + 1)
    response = HttpResponse(data, status=206, content_type=mimetypes.guess_type(full.name)[0] or "application/octet-stream")
    response["Content-Range"] = f"bytes {start}-{end}/{size}"
    response["Accept-Ranges"] = "bytes"
    response["Content-Length"] = str(len(data))
    return response
