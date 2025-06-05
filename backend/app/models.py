# pydantic models for request and response bodies

from pydantic import BaseModel, HttpUrl, field_validator
from typing import Literal
import re


class LLMModel(str):
    """Custom type for LLM model validation."""
    # No special validation needed here, just acts as a distinct type


class CloneRequest(BaseModel):
    """Request body for the website cloning endpoint (now used for generation)."""
    # This model is actually used by the /api/generate endpoint now
    raw_html_path: str # Expecting the path to the saved raw HTML
    model: Literal[
        'llama-3.3-70b-versatile',
        'gemini-2.5-pro-preview-05-06',
        'mixtral-8x7b-32768'
    ] = 'gemini-2.5-pro-preview-05-06' # Default model

    # Note: The URL validation is no longer relevant for this model as it takes a path


class ScrapeRequest(BaseModel):
    """Request body for the website scraping endpoint."""
    url: str

    @field_validator('url')
    def validate_url(cls, v):
        if not re.match(r"^https?://", v):
            raise ValueError("URL must start with http:// or https://")
        return v


class CloneResponse(BaseModel):
    # This model might need adjustment based on what you actually return
    html: str  # the fully inlined, cloned HTML document
    # You might want to add other fields returned by the endpoints
    # raw_html: str | None = None # If /api/scrape also returns raw HTML
    # generated_html: str | None = None # If /api/generate returns generated HTML
    raw_html_path: str | None = None
    generated_html_path: str | None = None
    debug_info: dict | None = None
    processing_time: float | None = None
    timestamp: str | None = None
