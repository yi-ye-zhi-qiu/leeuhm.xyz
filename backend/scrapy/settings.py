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
# DOWNLOAD_HANDLERS = {
#     "http": "scrapy_impersonate.ImpersonateDownloadHandler",
#     "https": "scrapy_impersonate.ImpersonateDownloadHandler",
# }
USER_AGENT = "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36"
# TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEEDS = {
    os.path.join(
        "azure://",  # upload to Azure
        "%(name)s",  # the Spider name, e.g. crawl-user-game-ids
        "%(_version)s",  # x.y.z
        "%(feeds_partition)s",  # /{region}/{tier}/, e.g. /euw/diamond/
        # /{region}/{user_name}/{user_tag} e.g. /na/ye qiu11/na1/
        "%(batch_time)s-%(batch_id)d.jsonl.gz",
    ): {
        "format": "jsonlines",
        "encoding": "utf-8",
        "store_empty": False,
        "postprocessing": ["crawl.postprocessing.GzipPlugin"],
        "gzip_compresslevel": 9,
        "batch_item_count": 150,  # every X games
    }
}
FEED_STORAGES = {"azure": "crawl.utils.feeds.AzureFeedStorage"}
AZURE_CONTAINER = os.environ["AZURE_CONTAINER"]
AZURE_ACCOUNT_URL = os.environ["AZURE_ACCOUNT_URL"]
AZURE_ACCOUNT_KEY = os.environ["AZURE_ACCOUNT_KEY"]
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
