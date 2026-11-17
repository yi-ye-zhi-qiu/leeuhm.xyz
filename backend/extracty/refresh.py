"""
Essentially orchestration -- nothing fancy here to warrant
Dagster/Airflow/etc.

This is just sequentially running spiders, as per:
https://docs.scrapy.org/en/latest/topics/practices.html

Call as a module.
"""

from scrapy.crawler import AsyncCrawlerRunner
from scrapy.utils.defer import deferred_f_from_coro_f
from scrapy.utils.reactor import install_reactor
from twisted.internet.task import react
from scrapy.utils.project import get_project_settings


from extracty.spiders.ugg import PlayerSpider, MatchSpider, MatchDetailSpider


async def crawl(_):
    runner = AsyncCrawlerRunner(get_project_settings())
    await runner.crawl(PlayerSpider, REGION="na1", N_LEADERBOARD_PAGES=1000)
    await runner.crawl(MatchSpider)
    await runner.crawl(MatchDetailSpider)


install_reactor()
react(deferred_f_from_coro_f(crawl))
