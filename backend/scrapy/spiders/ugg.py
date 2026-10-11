from crawl.endpoints import Region, UGGLeaderboard, UGGMatchDetail, UGGMatchSummary
from crawl.scrapy.items import LeaderboardItem, LeaderboardPlayerItem, MatchDetailItem
from scrapy import Spider
from scrapy.http import JsonRequest, Response
from typing import Iterable, Optional
from scrapy.utils.reactor import is_asyncio_reactor_installed


class CrawlLeaderboard(Spider):
    """
    A spider class to crawl UGG leaderboards and the top 20 games
    from each player. This will enable downstream crawl of game
    data.

    You can model the volume of games returned as n_pages * 100 * 20 * 10.
    This is because there are 100 players per page, 20 games per player,
    and 10 players per game. This assumes uniqueness across games and players.
    This is not the case! So, you'll likely end up with some fraction
    of that estimated volume.

    please invoke the spider with the `region` and `tier` spider arguments.

    `scrapy crawl ugg -a region=euw`

    # TODO: support tier selection ... maybe just with page limits?
    :param TIER: optional, the tier to crawl leaderboards
       from.  Possible values: challenger, grandmaster,
       master, diamond, emerald, platinum, gold, silver,
       bronze, iron. If no value is provided, defaults
       to None and is just the top X players.

    :param REGION: the region to crawl leaderboards from,
       possible values: euw, na, kr

    :param N_LEADERBOARD_PAGES: int value of how many leaderboard
       pages to scrape, has no max

    :param N_USER_ITER: int value of how many API requests to make
       per user; each iteration returns 20 more games, has no max
       though the API will time out eventually as OP.gg does not
       store user data for all time
    """

    name = "ugg-crawl-leaderboard"
    _version = "0.0.0"

    def __init__(
        self,
        REGION: Region,
        N_LEADERBOARD_PAGES: Optional[int],
        N_LEADERBOARD_PAGES_START_INDEX: Optional[int],
        N_USER_ITER: Optional[int],
        *args,
        **kwargs,
    ) -> None:
        # Check for correct asyncio reactor (allows JA3/Fingerprint impersonation)
        if not is_asyncio_reactor_installed():
            raise ValueError(
                f"{CrawlLeaderboard.__qualname__} requires the asyncio Twisted "
                f"reactor. Make sure you have it configured in the "
                f"TWISTED_REACTOR setting. See the asyncio documentation "
                f"of Scrapy for more information."
            )
        super(CrawlLeaderboard, self).__init__(*args, **kwargs)
        self.region: Region = REGION
        # Folder to partition by azure://data/euw/challenger/...
        # in the case of a null value: ....../euw/None/...
        self.feeds_partition = REGION
        self.n_leaderboard_pages = int(
            N_LEADERBOARD_PAGES or 7500
        )  # goes to bronze 1 about
        self.n_leaderboard_pages_start_index = int(N_LEADERBOARD_PAGES_START_INDEX or 1)
        self.n_user_iter = int(N_USER_ITER or 1)

    def start_requests(self) -> Iterable[JsonRequest]:
        for page_index in range(
            self.n_leaderboard_pages_start_index, self.n_leaderboard_pages + 1
        ):
            leaderboard = UGGLeaderboard()
            req = JsonRequest(
                url=leaderboard.url(),
                data=leaderboard.payload(region=self.region, page_index=page_index),
                callback=self.parse_leaderboard,
                errback=self.errback_bin,
            )
            yield req

    def parse_leaderboard(
        self, response: Response, page_index: int
    ) -> Iterable[JsonRequest]:
        for player in players:
            # TODO: should i yield an item instead?
            UGGLeaderboard.insert(response)
            for i in (1, self.n_user_iter):
                if not check_if_match_already_crawled():
                    matchsummary = UGGMatchSummary()
                    yield JsonRequest(
                        url=matchsummary.url(),
                        callback=self.parse_match_summary,
                        payload=matchsummary.payload(),
                        errback=self.errback_bin,
                    )

    def parse_match_summary(self, response: Response, riot_user_name: str):
        UGGMatchSummary.insert(response)
        for game in games:
            if not check_if_match_detail_already_crawled():
                matchdetail = UGGMatchDetail()
                yield JsonRequest(
                    url=matchdetail.url(),
                    payload=matchdetail.payload(),
                    callback=self.parse_match_detail,
                )

    def parse_match_detail(
        self, response: Response, match_id: str
    ) -> Iterable[MatchDetailItem]:
        self.logger.info("Got match detail for %s", match_id)
        yield UGGMatchDetail.insert(response)
