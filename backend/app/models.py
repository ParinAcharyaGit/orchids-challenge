# pydantic models for request and response bodies

from pydantic import BaseModel, HttpUrl, field_validator
from typing import Literal, List, Dict, Any # Import List, Dict, Any
import re


class LLMModel(str):
    """Custom type for LLM model validation."""
    # No special validation needed here, just acts as a distinct type


class ScrapeRequest(BaseModel):
    """Request body for the website scraping endpoint."""
    url: str

    @field_validator('url')
    def validate_url(cls, v):
        if not re.match(r"^https?://", v):
            raise ValueError("URL must start with http:// or https://")
        return v


class CloneRequest(BaseModel):
    """Request body for the website cloning endpoint (now used for generation)."""
    raw_html_path: str # Expecting the path to the saved raw HTML
    model: Literal[
        'llama-3.3-70b-versatile',
        'gemini-2.5-pro-preview-05-06',
        'mixtral-8x7b-32768'
    ] = 'gemini-2.5-pro-preview-05-06' # Default model

    # Note: The URL validation is no longer relevant for this model as it takes a path


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

# --- New Models for Editing Feature ---

class EditRequest(BaseModel):
    """Request body for the HTML editing endpoint."""
    html_content: str # The HTML to edit (can be raw or generated)
    instruction: str # The editing instruction from the user
    model: Literal[
        'gemini-2.5-pro-preview-05-06',
        # Add other editing models if needed, but prompt specified Gemini Pro
    ] = 'gemini-2.5-pro-preview-05-06' # Default/only model for editing

class EditResponse(BaseModel):
    """Response body for the HTML editing endpoint."""
    edited_html: str # The edited HTML content
    processing_time: float | None = None
    timestamp: str | None = None
    debug_info: dict | None = None # Optional debug info from LLM call

class LatestScrapedResponse(BaseModel):
    """Response body for getting the latest scraped file path."""
    latest_scraped_path: str | None = None
    error: str | None = None # Include error field if file not found
