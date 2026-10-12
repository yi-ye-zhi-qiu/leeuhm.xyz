from sqlalchemy import select

from crawl.endpoints import Region, UGGMatchDetail, UGGMatch, UGGPlayer
from scrapy import Spider
from scrapy.http import JsonRequest, Response
from typing import Iterable, Optional
from scrapy.utils.reactor import is_asyncio_reactor_installed

from endpoints import UGGMatch, UGGPlayer
from schemas import Match, make_player_id


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
        self.n_leaderboard_pages = int(
            N_LEADERBOARD_PAGES or 16043
        )  # every page on U.GG for NA1
        self.n_leaderboard_pages_start_index = int(N_LEADERBOARD_PAGES_START_INDEX or 1)
        self.n_user_iter = int(N_USER_ITER or 1)

    def start(self) -> Iterable[JsonRequest]:
        for page_index in range(
            self.n_leaderboard_pages_start_index, self.n_leaderboard_pages + 1
        ):
            leaderboard = UGGPlayer()
            req = JsonRequest(
                url=leaderboard.url(),
                data=leaderboard.payload(region=self.region, page_index=page_index),
                callback=self.parse_leaderboard,
                errback=self.errback_bin,
            )
            yield req

    def errback_bin(self, failure):
        self.logger.error(repr(failure))

    def parse_leaderboard(
        self, response: Response, page_index: int
    ) -> Iterable[JsonRequest]:
        UGGPlayer().insert(response=response, page_index=page_index)
        for player in response.json()["data"]["leaderboardPages"]["players"]:
            for i in (1, self.n_user_iter):
                match = UGGMatch()
                yield JsonRequest(
                    url=match.url(),
                    callback=self.parse_match_summary,
                    payload=match.payload(
                        region=self.region,
                        riot_tag_line=player["riotTagLine"],
                        riot_user_name=player["riotUserName"],
                        page_index=i,
                    ),
                    errback=self.errback_bin,
                    cb_kwargs={
                        "riot_user_name": player["riotUserLine"],
                        "riot_tag_line": player["riotTagLine"],
                    },
                )

    def parse_match_summary(
        self, response: Response, riot_user_name: str, riot_tag_line: str
    ):
        UGGMatch().insert(response)
        games = response.json()["data"]["fetchPlayerMatchSummaries"]["matchSummaries"]
        self.logger.info(
            "Got %d games for %s#%s", len(games), riot_user_name, riot_tag_line
        )
        for game in games:
            if select(Match).where(
                (Match.match_id == game["matchId"])
                & (Match.player_id == make_player_id(riot_user_name, riot_tag_line))
            ):
                continue
            match_detail = UGGMatchDetail(
                riot_user_name=riot_user_name,
                riot_tag_line=riot_tag_line,
                version=game["version"],
                match_id=game["matchId"],
                region=self.region,
            )
            yield JsonRequest(
                url=match_detail.url(),
                payload=match_detail.payload(),
                callback=self.parse_match_detail,
                cb_kwargs={"match_id": game["matchId"], "match_detail": match_detail},
            )

    def parse_match_detail(self, response: Response, match_id: str) -> None:
        self.logger.info("Got match detail for %s", match_id)
        match_detail.insert(response)
        return
