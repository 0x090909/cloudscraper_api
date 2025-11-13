"""curl_cffi service for handling web scraping requests with browser impersonation."""

import logging
import time
from typing import Dict, Optional
from curl_cffi.requests import AsyncSession, Response
from curl_cffi import CurlError

from app.models import ScrapeRequest, ScrapeResponse

logger = logging.getLogger(__name__)


class ScraperService:
    """Service class for handling web scraping with curl_cffi."""

    def __init__(self):
        """Initialize the scraper service."""
        self.session = None

    async def _get_session(self) -> AsyncSession:
        """Get or create an AsyncSession instance."""
        if self.session is None:
            self.session = AsyncSession()
        return self.session

    async def scrape_url(self, request: ScrapeRequest) -> ScrapeResponse:
        """
        Scrape a URL using curl_cffi with browser impersonation.

        Args:
            request: ScrapeRequest object containing scraping parameters

        Returns:
            ScrapeResponse object with the scraping results
        """
        session = await self._get_session()

        try:
            logger.info(f"Scraping URL: {request.url} with method: {request.method}")

            # Track request start time
            start_time = time.time()

            # Prepare request parameters
            kwargs = {
                'timeout': request.timeout,
                'impersonate': 'chrome',  # Impersonate Chrome browser (bypasses fingerprinting)
            }

            if request.headers:
                kwargs['headers'] = request.headers

            # Execute the request based on method
            if request.method == "GET":
                response: Response = await session.get(request.url, **kwargs)
            else:  # POST
                kwargs['data'] = request.data or {}
                response: Response = await session.post(request.url, **kwargs)

            # Calculate elapsed time
            elapsed_seconds = time.time() - start_time

            # Convert headers to dict
            response_headers = dict(response.headers)

            logger.info(f"Successfully scraped {request.url} - Status: {response.status_code}")

            return ScrapeResponse(
                success=True,
                url=request.url,
                status_code=response.status_code,
                content=response.text,
                headers=response_headers,
                elapsed_seconds=elapsed_seconds
            )

        except TimeoutError as e:
            logger.error(f"Timeout error scraping {request.url}: {str(e)}")
            return ScrapeResponse(
                success=False,
                url=request.url,
                error=f"Request timed out after {request.timeout} seconds"
            )

        except CurlError as e:
            logger.error(f"Curl error scraping {request.url}: {str(e)}")
            # Check for specific curl error codes
            error_msg = str(e)
            if "timed out" in error_msg.lower():
                return ScrapeResponse(
                    success=False,
                    url=request.url,
                    error=f"Request timed out: {error_msg}"
                )
            elif "redirect" in error_msg.lower():
                return ScrapeResponse(
                    success=False,
                    url=request.url,
                    error=f"Too many redirects: {error_msg}"
                )
            else:
                return ScrapeResponse(
                    success=False,
                    url=request.url,
                    error=f"Request failed: {error_msg}"
                )

        except Exception as e:
            logger.error(f"Unexpected error scraping {request.url}: {str(e)}", exc_info=True)
            return ScrapeResponse(
                success=False,
                url=request.url,
                error=f"Unexpected error: {str(e)}"
            )

    async def close(self):
        """Close the session and cleanup resources."""
        if self.session:
            await self.session.close()
            self.session = None


# Global instance
scraper_service = ScraperService()
