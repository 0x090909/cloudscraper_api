"""FastAPI application for web scraping with curl_cffi browser impersonation."""

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
    logger.info("Starting curl_cffi Scraper API service...")
    yield
    logger.info("Shutting down curl_cffi Scraper API service...")
    # Cleanup scraper session
    await scraper_service.close()


# Initialize FastAPI application
app = FastAPI(
    title="curl_cffi Scraper API",
    description="HTTP API for web scraping using curl_cffi with browser impersonation to bypass anti-bot protection",
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


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint returning API information."""
    return HealthResponse(
        status="healthy",
        version=__version__
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=__version__
    )


@app.post("/scrape", tags=["scraper"], response_model=ScrapeResponse, status_code=status.HTTP_200_OK)
async def scrape_url(request: ScrapeRequest):
    """
    Scrape a web page using curl_cffi with browser impersonation.

    This endpoint accepts a URL and optional parameters, then uses curl_cffi
    to fetch the page content with Chrome browser fingerprinting, bypassing anti-bot protection.

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
