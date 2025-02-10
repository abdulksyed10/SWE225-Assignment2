import requests
import cbor
import time

from utils.response import Response

# Create a session with connection pooling
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=10)
session.mount("http://", adapter)
session.mount("https://", adapter)

def download(url, config, logger=None):
    """ Downloads a URL using the caching proxy with connection pooling. """
    host, port = config.cache_server
    try:
        resp = session.get(
            f"http://{host}:{port}/",
            params=[("q", f"{url}"), ("u", f"{config.user_agent}")],
            timeout=5  # Set timeout to prevent hanging
        )
        
        if resp and resp.content:
            return Response(cbor.loads(resp.content))

    except requests.exceptions.RequestException as e:
        if logger:
            logger.error(f"Download failed for {url}: {e}")
        return Response({"error": str(e), "status": 500, "url": url})

    if logger:
        logger.error(f"Spacetime Response error {resp} with url {url}.")
    return Response({"error": f"Spacetime Response error {resp} with url {url}.", "status": resp.status_code, "url": url})
