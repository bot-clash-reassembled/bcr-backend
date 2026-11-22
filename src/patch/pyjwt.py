import gzip
import json
import logging
import urllib.request

from io import BytesIO

from typing import Any
from urllib.error import HTTPError, URLError

import jwt


logger = logging.getLogger(__name__)


class BcrPyJWKClient(jwt.PyJWKClient):
    def fetch_data(self) -> Any:
        """Fetch the JWK Set from the JWKS endpoint.

        Makes an HTTP request to the configured ``uri`` and returns the
        parsed JSON response. If the JWK Set cache is enabled, the
        response is stored in the cache.

        :returns: The parsed JWK Set as a dictionary.
        :raises PyJWKClientConnectionError: If the HTTP request fails.
        """
        try:
            r = urllib.request.Request(url=self.uri, headers=self.headers)
            with urllib.request.urlopen(
                r, timeout=self.timeout, context=self.ssl_context
            ) as response:
                jwk_set = self._wrap_json_load(response)
        except (URLError, TimeoutError) as e:
            if isinstance(e, HTTPError):
                e.close()
            raise jwt.PyJWKClientConnectionError(
                f'Fail to fetch data from the url, err: "{e}"'
            ) from e

        # Only update the cache on a successful fetch. Writing in a
        # `finally` block with `jwk_set=None` on error clears any
        # previously-cached JWKS, turning a transient outage into a cache
        # wipe that breaks legitimate auth.
        if self.jwk_set_cache is not None:
            self.jwk_set_cache.put(jwk_set)
        return jwk_set

    def _wrap_json_load(self, response):
        full_response = response.read()
        try:
            return json.load(BytesIO(full_response))
        except UnicodeDecodeError:
            # This is a known failure mode - even while Accept-Encoding is specified sometimes response is gzipped
            logger.debug(
                "UnicodeDecodeError while get_signing_key_from_jwt: probably received gzipped response, trying to uncompress..."
            )
            decompressed_response = gzip.decompress(full_response)
            return json.loads(decompressed_response)
