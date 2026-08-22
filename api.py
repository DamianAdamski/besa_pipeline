# api.py
import logging
import time
import requests

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 30       # seconds, avoid hanging forever on a stalled connection
MAX_RETRIES = 3            # total attempts for a transient failure
RETRY_BACKOFF_SECONDS = 2  # base backoff; grows with each retry attempt

def clickup_get(endpoint, headers, params=None, delay=0.3, max_retries=MAX_RETRIES):
    url = f"https://api.clickup.com/api/v2/{endpoint}"

    for attempt in range(1, max_retries + 1):
        try:
            res = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
        except requests.exceptions.RequestException as exc:
            if attempt == max_retries:
                logger.error("ClickUp request failed after %d attempts: %s (%s)", max_retries, url, exc)
                raise
            logger.warning("ClickUp request error on attempt %d/%d for %s: %s", attempt, max_retries, url, exc)
            time.sleep(RETRY_BACKOFF_SECONDS * attempt)
            continue

        if res.status_code == 200:
            time.sleep(delay)  # avoid rate limit
            return res.json()

        # Retry on rate limiting and transient server errors; fail fast on other 4xx errors
        if res.status_code == 429 or res.status_code >= 500:
            if attempt == max_retries:
                logger.error(
                    "ClickUp API error %d after %d attempts for %s: %s",
                    res.status_code, max_retries, url, res.text
                )
                raise Exception(f"ClickUp API error: {res.status_code} - {res.text}")

            logger.warning(
                "ClickUp API error %d on attempt %d/%d for %s: %s",
                res.status_code, attempt, max_retries, url, res.text
            )
            retry_after = res.headers.get("Retry-After")
            wait = float(retry_after) if retry_after else RETRY_BACKOFF_SECONDS * attempt
            time.sleep(wait)
            continue

        logger.error("ClickUp API error %d for %s: %s", res.status_code, url, res.text)
        raise Exception(f"ClickUp API error: {res.status_code} - {res.text}")
