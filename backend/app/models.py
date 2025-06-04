# pydantic models for request and response bodies

from pydantic import BaseModel, HttpUrl


class CloneRequest(BaseModel):
    url: HttpUrl  # ensures valid URL


class CloneResponse(BaseModel):
    html: str  # the fully inlined, cloned HTML document
