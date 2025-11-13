"""Pydantic models for request and response validation."""

from typing import Dict, Optional, Literal
from pydantic import BaseModel, HttpUrl, Field, field_validator


class ScrapeRequest(BaseModel):
    """Request model for scraping a web page."""

    url: str = Field(
        ...,
        description="The URL to scrape",
        examples=["https://example.com"]
    )
    method: Literal["GET", "POST"] = Field(
        default="GET",
        description="HTTP method to use"
    )
    headers: Optional[Dict[str, str]] = Field(
        default=None,
        description="Optional custom headers to send with the request"
    )
    timeout: int = Field(
        default=30,
        ge=1,
        le=120,
        description="Request timeout in seconds (1-120)"
    )
    data: Optional[Dict[str, str]] = Field(
        default=None,
        description="Optional data to send with POST requests"
    )

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate that the URL is properly formatted and uses http/https."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class ScrapeResponse(BaseModel):
    """Response model for scraping results."""

    success: bool = Field(
        ...,
        description="Whether the request was successful"
    )
    url: str = Field(
        ...,
        description="The URL that was scraped"
    )
    status_code: Optional[int] = Field(
        default=None,
        description="HTTP status code of the response"
    )
    content: Optional[str] = Field(
        default=None,
        description="The content of the scraped page"
    )
    headers: Optional[Dict[str, str]] = Field(
        default=None,
        description="Response headers from the server"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if the request failed"
    )
    elapsed_seconds: Optional[float] = Field(
        default=None,
        description="Time taken to complete the request"
    )


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(
        default="healthy",
        description="Service health status"
    )
    version: str = Field(
        ...,
        description="API version"
    )
