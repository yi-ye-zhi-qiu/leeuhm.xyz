import os

LOG_LEVEL = "INFO"
RETRY_ENABLED = False
COOKIES_ENABLED = False
SPIDER_MODULES = ["crawl.spiders"]
CONCURRENT_REQUESTS = 128
DOWNLOADER_MIDDLEWARES = {
    "crawl.middlewares.Proxy": 100,
    "crawl.middlewares.Impersonate": 200,
}
ITEM_PIPELINES = {
    "crawl.pipelines.RecordCrawledAt": 100,
}
EXTENSIONS = {
    "scrapy.extensions.feedexport.FeedExporter": None,
    "crawl.extensions.ImmediateFeedExporter": 0,
}
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
DOWNLOADER_CLIENT_TLS_METHOD = "TLSv1.2"
DOWNLOAD_HANDLERS = {
    "http": "scrapy_impersonate.ImpersonateDownloadHandler",
    "https": "scrapy_impersonate.ImpersonateDownloadHandler",
}
USER_AGENT = "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36"
DEFAULT_REQUEST_HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Authorization": "",
    "Content-Type": "application/json",
    "Dnt": "1",
    "Origin": "https://u.gg",
    "Priority": "u=1, i",
    "Referer": "https://u.gg/lol/leaderboards/ranking?region=na1",
    "Sec-Ch-Ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
    "Sec-Ch-Ua-Mobile": "?1",
    "Sec-Ch-Ua-Platform": '"Android"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
    "X-App-Type": "web",
    "X-App-Version": "43fbbe7cce4c6e5ca7278597788eefbe02e91992",
}
SPIDERMON_DISCORD_WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
