from sqlalchemy import select
from models import Match, Player, Region
from endpoints import UGGMatch, UGGMatchDetail, UGGPlayer
from scrapy.spiders import Spider
from scrapy.http import JsonRequest, Response
from typing import AsyncIterable, Iterable, Optional
from scrapy.utils.reactor import is_asyncio_reactor_installed


class PlayerSpider(Spider):
    """
    A spider class to crawl UGG `N_LEADERBOARD_PAGES` leaderboard pages
    and populate the `Player` database.

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

    name = "player-spider"

    # Version management policy: always run 'latest',
    # there is no SemVer here (https://semver.org/).
    __sem_ver_version = None

    def __init__(
        self,
        REGION: Region,
        N_LEADERBOARD_PAGES: Optional[int],
        *args,
        **kwargs,
    ) -> None:
        # Check for correct asyncio reactor (allows JA3/Fingerprint impersonation)
        if not is_asyncio_reactor_installed():
            raise ValueError(
                f"{PlayerSpider.__qualname__} requires the asyncio Twisted "
                f"reactor. Make sure you have it configured in the "
                f"TWISTED_REACTOR setting. See the asyncio documentation "
                f"of Scrapy for more information."
            )
        super(PlayerSpider, self).__init__(*args, **kwargs)
        self.region: Region = Region(REGION)
        self.n_leaderboard_pages = (
            int(N_LEADERBOARD_PAGES) if N_LEADERBOARD_PAGES else None
        )

    async def start(self) -> AsyncIterable[JsonRequest]:
        leaderboard = UGGPlayer()
        page_index = 1
        req = JsonRequest(
            url=leaderboard.url(),
            data=leaderboard.payload(region=self.region, page_index=page_index),
            callback=self.parse,
            errback=self.errback_bin,
            cb_kwargs={"page_index": page_index},
        )
        yield req

    def errback_bin(self, failure):
        # TODO: submit isometric error to Postgres & recrawl failed requests
        self.logger.error(repr(failure))

    async def parse(
        self, response: Response, page_index: int
    ) -> AsyncIterable[JsonRequest]:
        await UGGPlayer().insert(
            response=response, page_index=page_index, region=self.region
        )
        if response.meta.get("do_not_paginate"):
            return
        n_players = int(response.json()["data"]["leaderboardPage"]["totalPlayerCount"])
        page_size = len(response.json()["data"]["leaderboardPage"]["players"])
        n_pages = min(self.n_leaderboard_pages or n_players, n_players // 100)
        self.logger.info(
            "Crawling %d pages (%d players total, page size: %d)",
            n_pages,
            n_players,
            page_size,
        )
        for i in range(2, n_pages + 1):
            leaderboard = UGGPlayer()
            yield JsonRequest(
                url=leaderboard.url(),
                data=leaderboard.payload(region=self.region, page_index=i),
                callback=self.parse,
                errback=self.errback_bin,
                cb_kwargs={"page_index": i},
                meta={"do_not_paginate": True},
            )


class MatchSpider(Spider):
    name = "match-spider"

    def __init__(
        self,
        N_GAMES_PER_PLAYER: Optional[int],
        PLAYER_ID: Optional[str],
        *args,
        **kwargs,
    ) -> None:
        if not is_asyncio_reactor_installed():
            raise ValueError()
        super(MatchSpider, self).__init__(*args, **kwargs)
        self.player_id = PLAYER_ID
        self.n_games_per_player = N_GAMES_PER_PLAYER or 10

    async def start(self) -> AsyncIterable[JsonRequest]:
        # limit to specific player as desired
        players = select(
            Player.riot_tag_line, Player.riot_user_name, Player.region
        ).where(
            Player.player_id == self.player_id if self.player_id else True
        )
        for player in players:
            for i in (1, self.n_games_per_player):
                match = UGGMatch()
                yield JsonRequest(
                    url=match.url(),
                    callback=self.parse,
                    payload=match.payload(
                        region=player.region,
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

    def errback_bin(self, failure):
        self.logger.error(repr(failure))

    def parse(self, response: Response, riot_user_name: str, riot_tag_line: str):
        UGGMatch().insert(response)
        games = response.json()["data"]["fetchPlayerMatchSummaries"]["matchSummaries"]
        self.logger.info(
            "Got %d games for %s#%s", len(games), riot_user_name, riot_tag_line
        )


class MatchDetailSpider(Spider):
    name = "match-detail-spider"

    async def start(self) -> AsyncIterable[JsonRequest]:
        # select only matches where match detail for said player does not exist
        matches = select(
            Match.match_id,
            Match.riot_tag_line,
            Match.riot_user_name,
            Match.version,
            Match.match_id,
            Match.region_id,
        )
        for match in matches:
            match_detail = UGGMatchDetail(
                riot_user_name=match.riot_user_name,
                riot_tag_line=match.riot_tag_line,
                version=match.version,
                match_id=match.match_id,
                region=match.region_id,
            )
            yield JsonRequest(
                url=match_detail.url(),
                payload=match_detail.payload(),
                callback=self.parse,
                cb_kwargs={"match_id": match.match_id, "match_detail": match_detail},
                errback=self.errback_bin,
            )

    def errback_bin(self, failure):
        self.logger.error(repr(failure))

    def parse(
        self, response: Response, match_id: str, match_detail: UGGMatchDetail
    ) -> None:
        self.logger.info("Got match detail for %s", match_id)
        match_detail.insert(response)
        return
