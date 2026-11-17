from pathlib import Path

from config import settings
from extracty.items import UGGMatchDetailResponse, UGGMatchResponse, UGGPlayerResponse

LOG_LEVEL = "INFO"
RETRY_ENABLED = False
COOKIES_ENABLED = False
SPIDER_MODULES = ["extracty.spiders"]
CONCURRENT_REQUESTS = 128
DOWNLOADER_MIDDLEWARES = {
    "extracty.middlewares.Proxy": 100,
}
ITEM_PIPELINES = {
    "extracty.pipelines.RecordCrawledAt": 100,
    "spidermon.contrib.scrapy.pipelines.ItemValidationPipeline": 800,
}
# If you want to go the no proxy route, explore Camoufox for humanized behavior:
# https://scrapy-playwright.readthedocs.io/en/latest/setup.html#setup
# DOWNLOAD_HANDLERS = {
#     "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
#     # "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
# }
# TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
# PLAYWRIGHT_PROCESS_REQUEST_HEADERS = None
# PLAYWRIGHT_BROWSER_PROVIDER = "extracty.providers.CamoufoxBrowserProvider"
# # Camoufox is a firefox browser
# PLAYWRIGHT_BROWSER_TYPE = "firefox"
# PLAYWRIGHT_LAUNCH_OPTIONS = {"headless": True, "humanize": True}
EXTENSIONS = {
    "spidermon.contrib.scrapy.extensions.Spidermon": 500,
}
DEFAULT_REQUEST_HEADERS = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9",
    "authorization": "",
    "content-type": "application/json",
    "dnt": "1",
    "origin": "https://u.gg",
    "priority": "u=1, i",
    "referer": "https://u.gg/lol/leaderboards/ranking?region=na1&page=49",
    "sec-ch-ua": '"Not-A.Brand";v="99", "Google Chrome";v="157", "Chromium";v="157"',
    "sec-ch-ua-mobile": "?1",
    "sec-ch-ua-platform": '"Android"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Linux; Android 16; Pixel 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Mobile Safari/537.36",
    "x-app-type": "web",
    "x-app-version": "289fe635ad46ee7b6b830d86b4106d8baafc9371",
}
SPIDERMON_ENABLED = True
SPIDERMON_DISCORD_WEBHOOK_URL = settings.discord_webhook_url
SPIDERMON_MAX_EXECUTION_TIME = 5 * 60  # 5 minutes
SPIDERMON_MAX_ERRORS_PERIODIC = 100
SPIDERMON_MAX_ERRORS = 100
SPIDERMON_DISCORD_MESSAGE_TEMPLATE = str(
    Path(__file__).parent / "discord_notification.jinja"
)
SPIDERMON_PERIODIC_MONITORS = {
    # number of seconds between each monitoring check
    "extracty.monitors.PeriodicMonitorSuite": 60,
}
SPIDERMON_UNWANTED_HTTP_CODES = {
    # Fail if there are more than `min(100, 0.1 * total_requests)` 403 responses (10%)
    403: {"max_count": 100, "max_percentage": 0.1},
}
SPIDERMON_ITEM_COUNT_INCREASE = 1
SPIDERMON_VALIDATION_SCHEMAS = {
    UGGPlayerResponse: str(Path(__file__).parent / "schemas" / "player.json"),
    UGGMatchResponse: str(Path(__file__).parent / "schemas" / "match.json"),
    UGGMatchDetailResponse: str(
        Path(__file__).parent / "schemas" / "match_detail.json"
    ),
}
SPIDERMON_SPIDER_CLOSE_MONITORS = ("extracty.monitors.SpiderCloseMonitorSuite",)
ASSETS_BUCKET = settings.assets_bucket
R2_ENDPOINT_URL = settings.r2_endpoint_url
R2_ACCESS_KEY_ID = settings.r2_access_key_id
R2_SECRET_ACCESS_KEY = settings.r2_secret_access_key
