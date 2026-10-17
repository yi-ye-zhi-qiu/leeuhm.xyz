from db import AsyncSessionLocal
from sqlalchemy import func, select
from models import Match, MatchDetail, Player
from schemas import Region
from endpoints import UGGMatch, UGGMatchDetail, UGGPlayer
from extracty.items import UGGMatchDetailResponse, UGGMatchResponse, UGGPlayerResponse
from scrapy.spiders import Spider
from scrapy.http import JsonRequest, Response
from typing import AsyncIterable, Iterable, Optional
from scrapy.utils.reactor import is_asyncio_reactor_installed


def record_rows_written(stats, table: str, n_rows: int) -> None:
    stats.inc_value("db/rows_written", count=n_rows)
    stats.inc_value(f"db/rows_written/{table}", count=n_rows)


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
    ) -> AsyncIterable[UGGPlayerResponse | JsonRequest]:
        yield UGGPlayerResponse(response.json())
        n_written = await UGGPlayer().insert(
            response=response, page_index=page_index, region=self.region
        )
        record_rows_written(self.crawler.stats, "player", n_written)
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
        N_GAMES_PER_PLAYER: Optional[int] = None,
        PLAYER_ID: Optional[str] = None,
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
        async with AsyncSessionLocal.begin() as session:
            players = (
                await session.execute(
                    select(Player.riot_tag_line, Player.riot_user_name, Player.region)
                    .where(
                        Player.player_id == self.player_id if self.player_id else True
                    )
                    .limit(2)
                )
            ).all()
        self.logger.info("Found %d players", len(players))
        for player in players:
            riot_tag_line, riot_user_name, region = player
            for i in (1, self.n_games_per_player):
                match = UGGMatch()
                yield JsonRequest(
                    url=match.url(),
                    callback=self.parse,
                    data=match.payload(
                        region=region,
                        riot_tag_line=riot_tag_line,
                        riot_user_name=riot_user_name,
                        page_index=i,
                    ),
                    errback=self.errback_bin,
                    cb_kwargs={
                        "riot_user_name": riot_user_name,
                        "riot_tag_line": riot_tag_line,
                    },
                )

    def errback_bin(self, failure):
        self.logger.error(repr(failure))

    async def parse(
        self, response: Response, riot_user_name: str, riot_tag_line: str
    ) -> AsyncIterable[UGGMatchResponse]:
        yield UGGMatchResponse(response.json())
        n_written = await UGGMatch().insert(response)
        record_rows_written(self.crawler.stats, "match", n_written)
        games = response.json()["data"]["fetchPlayerMatchSummaries"]["matchSummaries"]
        self.logger.info(
            "Got %d games for %s#%s", len(games), riot_user_name, riot_tag_line
        )


class MatchDetailSpider(Spider):
    name = "match-detail-spider"

    def __init__(
        self,
        N_REQUESTS_CAP: Optional[int] = None,
        *args,
        **kwargs,
    ) -> None:
        if not is_asyncio_reactor_installed():
            raise ValueError()
        super(MatchDetailSpider, self).__init__(*args, **kwargs)
        self.n_requests_cap = int(N_REQUESTS_CAP) if N_REQUESTS_CAP else None

    async def start(self) -> AsyncIterable[JsonRequest]:
        participant_id = func.unnest(Match.player_ids).label("player_id")
        participants = select(
            Match.match_id, Match.version, Match.region_id, participant_id
        ).subquery()
        stmt = (
            select(
                participants.c.match_id,
                participants.c.version,
                participants.c.region_id,
                Player.riot_user_name,
                Player.riot_tag_line,
            )
            .join(Player, Player.player_id == participants.c.player_id)
            .where(
                ~select(MatchDetail.match_id)
                .where(
                    MatchDetail.match_id == participants.c.match_id,
                    MatchDetail.player_id == participants.c.player_id,
                )
                .exists()
            )
            .limit(self.n_requests_cap)
        )
        async with AsyncSessionLocal() as session:
            pairs = (await session.execute(stmt)).all()
        self.logger.info("Found %d match details to crawl", len(pairs))
        for match_id, version, region, riot_user_name, riot_tag_line in pairs:
            match_detail = UGGMatchDetail(
                riot_user_name=riot_user_name,
                riot_tag_line=riot_tag_line,
                version=version,
                match_id=match_id,
                region=region,
            )
            yield JsonRequest(
                url=match_detail.url(),
                data=match_detail.payload(),
                callback=self.parse,
                cb_kwargs={"match_id": match_id, "match_detail": match_detail},
                errback=self.errback_bin,
            )

    def errback_bin(self, failure):
        self.logger.error(repr(failure))

    async def parse(
        self, response: Response, match_id: str, match_detail: UGGMatchDetail
    ) -> AsyncIterable[UGGMatchDetailResponse]:
        yield UGGMatchDetailResponse(response.json())
        n_written = await match_detail.insert(response)
        for table, n_rows in n_written.items():
            record_rows_written(self.crawler.stats, table, n_rows)
        self.logger.info(
            "Got match detail for %s (%s#%s)",
            match_id,
            match_detail.riot_user_name,
            match_detail.riot_tag_line,
        )
