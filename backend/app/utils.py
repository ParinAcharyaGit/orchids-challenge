# helper functions like image conversion to URIs.

import base64
from urllib.parse import urljoin
from fastapi import HTTPException


def to_data_uri(mime_type: str, data_bytes: bytes) -> str:
    """
    Convert raw bytes into a data URI, e.g. "data:image/png;base64,...."
    """
    b64 = base64.b64encode(data_bytes).decode("utf-8")
    return f"data:{mime_type};base64,{b64}"


def resolve_url(base_url: str, src: str) -> str:
    """
    Given a base page URL and a possibly relative `src`,
    return an absolute URL. Raises HTTPException on invalid.
    """
    try:
        return urljoin(base_url, src)
    except Exception:
        raise HTTPException(status_code=400, detail=f"Invalid resource URL: {src}")
