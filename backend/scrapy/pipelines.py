from datetime import datetime, timezone


class RecordCrawledAt:

    def process_item(self, item, spider):
        item["crawled_at"] = (
            datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        )
        return item
