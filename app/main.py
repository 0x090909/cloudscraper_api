"""FastAPI application for web scraping with cloudscraper."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.models import ScrapeRequest, ScrapeResponse, HealthResponse
from app.scraper import scraper_service
from app import __version__

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    logger.info("Starting Cloudscraper API service...")
    yield
    logger.info("Shutting down Cloudscraper API service...")


# Initialize FastAPI application
app = FastAPI(
    title="Cloudscraper API",
    description="HTTP API for web scraping using cloudscraper to bypass Cloudflare protection",
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/scrape", tags=["cloudscrape"],response_model=ScrapeResponse, status_code=status.HTTP_200_OK)
async def scrape_url(request: ScrapeRequest):
    """
    Scrape a web page using cloudscraper.

    This endpoint accepts a URL and optional parameters, then uses cloudscraper
    to fetch the page content, automatically bypassing Cloudflare protection if present.

    Args:
        request: ScrapeRequest containing the URL and optional parameters

    Returns:
        ScrapeResponse with the scraped content and metadata

    Example:
        ```json
        {
            "url": "https://example.com",
            "method": "GET",
            "timeout": 30
        }
        ```
    """
    logger.info(f"Received scrape request for URL: {request.url}")

    try:
        result = await scraper_service.scrape_url(request)
        return result

    except Exception as e:
        logger.error(f"Unexpected error in scrape endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "An unexpected error occurred",
            "detail": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
