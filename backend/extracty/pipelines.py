import asyncio
import mimetypes
from datetime import datetime, timezone
from pathlib import Path

import boto3
from extracty.items import AssetItem


class RecordCrawledAt:

    def process_item(self, item, spider):
        item["crawled_at"] = (
            datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        )
        return item


class CloudfareR2StorageConnector:
    """
    This is used to store website assets. A spider will yield
    an `AssetItem` which gets stored in Cloudflare R2, which has
    the same backend as AWS S3.

    So, this class kind of meshes those together.

    Returns: e.g. `item/3158.png` in the `leeuhmxyz-assets` bucket.
    """

    def __init__(self, settings, stats):
        self.stats = stats
        self.bucket = settings.get("ASSETS_BUCKET")
        self.r2 = boto3.client(
            "s3",
            endpoint_url=settings.get("R2_ENDPOINT_URL"),
            aws_access_key_id=settings.get("R2_ACCESS_KEY_ID"),
            aws_secret_access_key=settings.get("R2_SECRET_ACCESS_KEY"),
            region_name="auto",
        )

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings, crawler.stats)

    async def process_item(self, item: AssetItem):
        # e.g. `image/svg+xml`, which `<img>` needs to render an SVG
        content_type, _ = mimetypes.guess_type(item["key"])
        # boto3 is blocking
        await asyncio.to_thread(
            self.r2.put_object,
            Bucket=self.bucket,
            Key=item["key"],
            Body=item["body"],
            ContentType=content_type or "application/octet-stream",
        )
        self.stats.inc_value("assets/stored")
        return item
