from config import settings


class Proxy:
    """
    A middleware to use a proxy url.

    You absolutely need to do this in this day and age. Even if you use Scrapy Playwright
    with Camoufox and humanize requests, your rate will be painfully slow, which you then pay
    for in terms of parallel compute.

    What proxy provider you choose is up to you, this will cost ~$20/month.
    """

    def process_request(self, request, spider):
        if not request.meta.get("proxy", None) and settings.proxy_network_url:
            request.meta["proxy"] = settings.proxy_network_url
