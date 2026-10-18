import hashlib
import mimetypes
from datetime import datetime, timezone
from io import BytesIO

from scrapy.pipelines.files import FilesPipeline
from scrapy.utils.defer import ensure_awaitable


class RecordCrawledAt:

    def process_item(self, item, spider):
        item["crawled_at"] = (
            datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        )
        return item


class AssetFilesPipeline(FilesPipeline):

    def file_path(self, request, response=None, info=None, *, item=None):
        return item["keys"][0]

    async def file_downloaded(self, response, request, info, *, item=None):
        for path in item["keys"]:
            content_type, _ = mimetypes.guess_type(path)
            await ensure_awaitable(
                self.store.persist_file(
                    path,
                    BytesIO(response.body),
                    info,
                    headers={
                        "Content-Type": content_type or "application/octet-stream"
                    },
                )
            )
        return hashlib.md5(response.body).hexdigest()
