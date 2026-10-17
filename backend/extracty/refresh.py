"""
Essentially orchestration -- nothing fancy here to warrant
Dagster/Airflow/etc.
"""

from scrapy.crawler import CrawlerProcess
from twisted.internet import defer
from twisted.internet import asyncioreactor
from scrapy.utils.log import configure_logging
from scrapy.utils.reactor import install_reactor
from scrapy.utils.project import get_project_settings

configure_logging()
settings = get_project_settings()
process = CrawlerProcess(settings)

# Installation of asyncio reactor as per `CrawlerRunner`
# https://docs.scrapy.org/en/latest/topics/asyncio.html#installing-the-asyncio-reactor
reactor = asyncioreactor.AsyncioSelectorReactor()
install_reactor("twisted.internet.asyncioreactor.AsyncioSelectorReactor")


# Sequential run of spiders, one runs after the prior completes
@defer.inlineCallbacks
def crawl():
    yield process.crawl("player-spider", N_LEADERBOARD_PAGES=1)
    yield process.crawl("match-spider", N_GAMES_PER_PLAYER=1)
    yield process.crawl("match-detail-spider")
    process.stop()


crawl()
# reactor.run()  # the script will block here until the last crawl call is finished
process.start()
