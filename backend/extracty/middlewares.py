import os

# TODO: store this as a secret
PROXY_NETWORK_URL = os.getenv("PROXY_NETWORK_URL")


class Proxy:
    """A middleware to use a proxy url."""

    def process_request(self, request, spider):
        if not request.meta.get("proxy", None) and PROXY_NETWORK_URL:
            request.meta["proxy"] = PROXY_NETWORK_URL


class Impersonate:
    """A middleware to impersonate a browser."""

    def process_request(self, request, spider):
        request.meta.setdefault("impersonate", "chrome")
        return None
