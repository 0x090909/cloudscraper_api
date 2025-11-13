"""curl_cffi service for handling web scraping requests with browser impersonation.

This service implements explicit Cloudflare bypass techniques using curl_cffi's
browser impersonation capabilities, including:

1. TLS/JA3 Fingerprinting: Mimics real Chrome browser TLS handshakes
2. HTTP/2 Fingerprinting: Replicates Chrome's HTTP/2 connection parameters
3. Browser Headers: Uses authentic browser headers (User-Agent, Accept, Sec-Ch-Ua, etc.)
4. Proxy Support: Enables IP rotation to avoid IP-based blocks

Key Points for Cloudflare Bypass:
- Use latest Chrome versions (chrome131+) for current fingerprints
- Let curl_cffi handle headers automatically (default_headers=True)
- TLS fingerprints alone may not bypass advanced Cloudflare (depends on protection level)
- Combine with good proxy IPs for better success rates
- Cloudflare uses multiple signals: TLS, IP quality, request rate, JS challenges
"""

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
        Scrape a URL using curl_cffi with explicit Cloudflare bypass techniques.

        This method implements browser impersonation to bypass anti-bot systems:
        - Impersonates real Chrome browser TLS/JA3 and HTTP/2 fingerprints
        - Uses authentic browser headers automatically
        - Supports proxy rotation for IP-based block bypass
        - Handles advanced fingerprinting that pure Python clients cannot

        Args:
            request: ScrapeRequest object containing scraping parameters

        Returns:
            ScrapeResponse object with the scraping results

        Notes:
            - For Cloudflare: Use chrome131+ for latest fingerprints
            - Keep default_headers=True to use curl_cffi's browser headers
            - Consider using proxies for better success against IP-based blocks
            - Success depends on site's protection level (basic vs advanced Cloudflare)
        """
        session = await self._get_session()

        try:
            logger.info(
                f"Scraping URL: {request.url} | Method: {request.method} | "
                f"Impersonate: {request.impersonate} | Proxy: {'Yes' if request.proxy else 'No'}"
            )

            # Track request start time
            start_time = time.time()

            # Prepare request parameters with Cloudflare bypass optimizations
            kwargs = {
                'timeout': request.timeout,
                'impersonate': request.impersonate,  # Browser fingerprint impersonation
                'default_headers': request.default_headers,  # Use curl_cffi's authentic browser headers
            }

            # Add proxy if provided (important for IP-based Cloudflare blocks)
            if request.proxy:
                kwargs['proxies'] = {
                    'http': request.proxy,
                    'https': request.proxy
                }
                logger.debug(f"Using proxy: {request.proxy}")

            # Add custom headers (will override default headers if default_headers=True)
            if request.headers:
                kwargs['headers'] = request.headers
                logger.debug(f"Using custom headers: {list(request.headers.keys())}")

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

            # Check for common Cloudflare indicators
            cf_ray = response_headers.get('cf-ray', '')
            server = response_headers.get('server', '').lower()
            is_cloudflare = 'cloudflare' in server or bool(cf_ray)

            logger.info(
                f"Successfully scraped {request.url} - Status: {response.status_code} | "
                f"Cloudflare: {'Yes' if is_cloudflare else 'No'} | "
                f"Time: {elapsed_seconds:.2f}s"
            )

            if is_cloudflare and response.status_code == 200:
                logger.info(f"✓ Cloudflare bypass successful for {request.url}")
            elif is_cloudflare and response.status_code in [403, 503]:
                logger.warning(f"⚠ Possible Cloudflare block on {request.url} (Status: {response.status_code})")

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
