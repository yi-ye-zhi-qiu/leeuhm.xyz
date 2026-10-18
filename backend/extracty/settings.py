import os
from pathlib import Path

from extracty.items import UGGMatchDetailResponse, UGGMatchResponse, UGGPlayerResponse

LOG_LEVEL = "INFO"
RETRY_ENABLED = False
COOKIES_ENABLED = False
SPIDER_MODULES = ["extracty.spiders"]
CONCURRENT_REQUESTS = 128
DOWNLOADER_MIDDLEWARES = {
    "extracty.middlewares.Proxy": 100,
    "extracty.middlewares.Impersonate": 200,
}
ITEM_PIPELINES = {
    "extracty.pipelines.RecordCrawledAt": 100,
    "spidermon.contrib.scrapy.pipelines.ItemValidationPipeline": 800,
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
EXTENSIONS = {
    "spidermon.contrib.scrapy.extensions.Spidermon": 500,
}
SPIDERMON_ENABLED = True
SPIDERMON_DISCORD_WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
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
SPIDERMON_SPIDER_CLOSE_MONITORS =("extracty.monitors.SpiderCloseMonitorSuite",)

# Assets (e.g. champion icons) are stored in Cloudflare R2, which is S3
# compatible, in a bucket per environment
ASSETS_BUCKET = os.environ.get("ASSETS_BUCKET", "espresso-assets-dev")
# Store assets in a local directory instead, e.g. for testing
ASSETS_LOCAL_DIR = os.environ.get("ASSETS_LOCAL_DIR")
R2_ENDPOINT_URL = (
    f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com"
    if "R2_ACCOUNT_ID" in os.environ
    else None
)
R2_ACCESS_KEY_ID = os.environ.get("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.environ.get("R2_SECRET_ACCESS_KEY")
