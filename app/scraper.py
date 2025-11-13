"""Cloudscraper service for handling web scraping requests."""

import logging
from typing import Dict, Optional
import cloudscraper
from requests.exceptions import RequestException, Timeout, TooManyRedirects, HTTPError

from app.models import ScrapeRequest, ScrapeResponse

logger = logging.getLogger(__name__)


class ScraperService:
    """Service class for handling web scraping with cloudscraper."""

    def __init__(self):
        """Initialize the scraper service."""
        self.scraper = None

    def _get_scraper(self) -> cloudscraper.CloudScraper:
        """Get or create a cloudscraper instance."""
        if self.scraper is None:
            self.scraper = cloudscraper.create_scraper(
                # Challenge handling
                interpreter='js2py',  # Best compatibility for v3 challenges
                delay=5,  # Extra time for complex challenges
                # Stealth mode
                enable_stealth=True,
                # Browser emulation
                browser='chrome',
            )
        return self.scraper

    async def scrape_url(self, request: ScrapeRequest) -> ScrapeResponse:
        """
        Scrape a URL using cloudscraper.

        Args:
            request: ScrapeRequest object containing scraping parameters

        Returns:
            ScrapeResponse object with the scraping results
        """
        scraper = self._get_scraper()

        try:
            logger.info(f"Scraping URL: {request.url} with method: {request.method}")

            # Prepare request parameters
            kwargs = {
                'timeout': request.timeout,
            }

            if request.headers:
                kwargs['headers'] = request.headers

            # Execute the request based on method
            if request.method == "GET":
                response = scraper.get(request.url, **kwargs)
            else:  # POST
                kwargs['data'] = request.data or {}
                response = scraper.post(request.url, **kwargs)

            # Convert headers to dict (response.headers is a CaseInsensitiveDict)
            response_headers = dict(response.headers)

            logger.info(f"Successfully scraped {request.url} - Status: {response.status_code}")

            return ScrapeResponse(
                success=True,
                url=request.url,
                status_code=response.status_code,
                content=response.text,
                headers=response_headers,
                elapsed_seconds=response.elapsed.total_seconds()
            )

        except Timeout as e:
            logger.error(f"Timeout error scraping {request.url}: {str(e)}")
            return ScrapeResponse(
                success=False,
                url=request.url,
                error=f"Request timed out after {request.timeout} seconds"
            )

        except TooManyRedirects as e:
            logger.error(f"Too many redirects for {request.url}: {str(e)}")
            return ScrapeResponse(
                success=False,
                url=request.url,
                error="Too many redirects"
            )

        except HTTPError as e:
            logger.error(f"HTTP error scraping {request.url}: {str(e)}")
            return ScrapeResponse(
                success=False,
                url=request.url,
                status_code=e.response.status_code if e.response else None,
                error=f"HTTP Error: {str(e)}"
            )

        except RequestException as e:
            logger.error(f"Request error scraping {request.url}: {str(e)}")
            return ScrapeResponse(
                success=False,
                url=request.url,
                error=f"Request failed: {str(e)}"
            )

        except Exception as e:
            logger.error(f"Unexpected error scraping {request.url}: {str(e)}", exc_info=True)
            return ScrapeResponse(
                success=False,
                url=request.url,
                error=f"Unexpected error: {str(e)}"
            )


# Global instance
scraper_service = ScraperService()
