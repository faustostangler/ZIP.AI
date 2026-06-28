import logging

import httpx

from src.ports.unsubscribe import UnsubscribePort

logger = logging.getLogger("zip.unsubscribe")


class HttpUnsubscribeAdapter(UnsubscribePort):
    """
    Adapter implementing UnsubscribePort using httpx client for HTTP GET requests.
    """

    def __init__(self, client: httpx.Client | None = None) -> None:
        self.client = client or httpx.Client(timeout=10.0)

    def unsubscribe(self, url: str) -> bool:
        logger.info(f"Attempting automated unsubscribe by requesting: {url}")
        try:
            # Send GET request, follow redirects
            response = self.client.get(url, follow_redirects=True)
            logger.info(f"Unsubscribe request returned HTTP {response.status_code}")
            return response.status_code < 400
        except Exception as e:
            logger.error(f"Failed to request unsubscribe URL {url}: {e}")
            return False
