"""Main interface for bronze data, requests/Scrapy are just busses."""

from datetime import time
import os
from alembic.context import execute
import scrapy.http
import logging
import requests
import psycopg2
from typing import Any, Literal, Optional, Union
from collections import namedtuple
from urllib.parse import urlunparse

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql.functions import now

from db import AsyncSessionLocal
from exceptions import FailedRequest
from models import (
    MetricEvent,
    Player,
    Match,
    MatchDetail,
    StatDeltaEvent,
    Team,
    TimelineEvent,
)
from schemas import (
    GameVersion,
    QueueType,
    Rank,
    Region,
    StatDelta,
    TeamId,
    Tier,
    make_player_id,
    make_team_id,
)

QUEUE_TYPE = 420  # 5v5 Summoner's rift
SEASON_IDS = [25, 26]  # Most recent (31-Aug-2026 2 seasons)

URLComponents = namedtuple(
    typename="URLComponents",
    field_names=["scheme", "netloc", "path", "params", "query", "fragment"],
)  # builder pattern


def response_status(
    response: Union[scrapy.http.Response, requests.Response],
) -> Union[int, Exception]:
    if isinstance(response, scrapy.http.Response):
        return response.status
    if isinstance(response, requests.Response):
        return response.status_code
    raise TypeError(f"unsupported response type: {type(response)!r}")


def position_columns(position: Optional[list[dict[str, Any]]]) -> dict[str, Any]:
    """`models.Position` columns from u.gg's position, e.g. `[{"x": 603, "y": 611}]`."""
    point = position[0] if position else {}
    return {"position_x": point.get("x"), "position_y": point.get("y")}


class UGGPlayer:
    def url(self) -> str:
        return str(
            urlunparse(
                URLComponents(
                    scheme="https",
                    netloc="u.gg",
                    path="/api",
                    params="",
                    query={},
                    fragment="",
                )
            )
        )

    def payload(self, page_index: int, region: Region) -> dict[str, Any]:
        return {
            "operationName": "getRankedLeaderboard",
            "variables": {
                "page": page_index,
                "queueType": QUEUE_TYPE,
                "regionId": Region(region).value,
            },
            "query": "query getRankedLeaderboard($page: Int, $queueType: Int, $regionId: String!) {\n  leaderboardPage(page: $page, queueType: $queueType, regionId: $regionId) {\n    totalPlayerCount\n    topPlayerMostPlayedChamp\n    players {\n      iconId\n      losses\n      lp\n      overallRanking\n      rank\n      summonerLevel\n      riotTagLine\n      riotUserName\n      tier\n      wins\n      __typename\n    }\n    __typename\n  }\n}",
        }

    async def insert(
        self,
        response: Union[scrapy.http.Response, requests.Response],
        page_index: int,
        region: Region,
    ) -> int:
        """Returns the number of rows written (inserted or updated)."""
        if response_status(response) != 200:
            raise FailedRequest()
        players = response.json()["data"]["leaderboardPage"]["players"]
        logging.info("Found %d players on page index %d", len(players), page_index)
        rows = []
        for player in players:
            rows.append(
                {
                    "player_id": make_player_id(
                        riot_user_name=player["riotUserName"],
                        riot_tag_line=player["riotTagLine"],
                    ),
                    "riot_user_name": player["riotUserName"],
                    "riot_tag_line": player["riotTagLine"],
                    "icon_id": player["iconId"],
                    "losses": int(player["losses"]),
                    "wins": int(player["wins"]),
                    # if unranked these values are null
                    "lp": int(player["lp"]) if player["lp"] is not None else None,
                    "rank": Rank(player["rank"].lower()) if player["rank"] else None,
                    "tier": Tier(player["tier"].lower()) if player["tier"] else None,
                    "summoner_level": player["summonerLevel"],
                    "region": Region(region),
                }
            )
        if not rows:
            return 0
        # Player is a latest table
        stmt = insert(Player)
        stmt = stmt.on_conflict_do_update(
            index_elements=["player_id"],
            set_=dict(
                icon_id=stmt.excluded["icon_id"],
                losses=stmt.excluded["losses"],
                lp=stmt.excluded["lp"],
                rank=stmt.excluded["rank"],
                tier=stmt.excluded["tier"],
                wins=stmt.excluded["wins"],
                summoner_level=stmt.excluded["summoner_level"],
                region=stmt.excluded["region"],
                updated_at=now(),
            ),
        )
        # Batch insert is faster, see:
        # https://stackoverflow.com/questions/3659142/bulk-insert-with-sqlalchemy-orm
        # https://docs.sqlalchemy.org/en/21/orm/persistence_techniques.html#bulk-operations
        # RETURNING gives one row per row written, `rowcount` isn't reliable
        # for bulk (executemany) statements
        async with AsyncSessionLocal.begin() as session:
            written = await session.scalars(stmt.returning(Player.player_id), rows)
            return len(written.all())


class UGGMatch:
    def url(self) -> str:
        return str(
            urlunparse(
                URLComponents(
                    scheme="https",
                    netloc="u.gg",
                    path="/api",
                    params="",
                    query={},
                    fragment="",
                )
            )
        )

    def payload(
        self, region: Region, riot_tag_line: str, riot_user_name: str, page_index: int
    ) -> dict[str, Any]:
        return {
            "operationName": "FetchMatchSummaries",
            "variables": {
                "regionId": Region(region).value,
                "riotUserName": riot_user_name,
                "riotTagLine": riot_tag_line,
                "queueType": [],
                "duoRiotUserName": "",
                "duoRiotTagLine": "",
                "role": [],
                "seasonIds": SEASON_IDS,
                "championId": [],
                "page": int(page_index),
            },
            "query": "query FetchMatchSummaries($championId: [Int], $page: Int, $queueType: [Int], $duoRiotUserName: String, $duoRiotTagLine: String, $regionId: String!, $role: [Int], $seasonIds: [Int]!, $riotUserName: String!, $riotTagLine: String!) {\n  fetchPlayerMatchSummaries(\n    championId: $championId\n    page: $page\n    queueType: $queueType\n    duoRiotUserName: $duoRiotUserName\n    duoRiotTagLine: $duoRiotTagLine\n    regionId: $regionId\n    role: $role\n    seasonIds: $seasonIds\n    riotUserName: $riotUserName\n    riotTagLine: $riotTagLine\n  ) {\n    finishedMatchSummaries\n    totalNumMatches\n    matchSummaries {\n      assists\n      augments\n      championId\n      cs\n      damage\n      deaths\n      gold\n      items\n      jungleCs\n      killParticipation\n      kills\n      level\n      matchCreationTime\n      matchDuration\n      matchId\n      maximumKillStreak\n      primaryStyle\n      queueType\n      regionId\n      role\n      runes\n      subStyle\n      summonerName\n      riotUserName\n      riotTagLine\n      summonerSpells\n      psHardCarry\n      psTeamPlay\n      lpInfo {\n        lp\n        placement\n        promoProgress\n        promoTarget\n        promotedTo {\n          tier\n          rank\n          __typename\n        }\n        __typename\n      }\n      teamA {\n        championId\n        summonerName\n        riotUserName\n        riotTagLine\n        teamId\n        role\n        hardCarry\n        teamplay\n        placement\n        playerSubteamId\n        __typename\n      }\n      teamB {\n        championId\n        summonerName\n        riotUserName\n        riotTagLine\n        teamId\n        role\n        hardCarry\n        teamplay\n        placement\n        playerSubteamId\n        __typename\n      }\n      version\n      visionScore\n      win\n      roleQuestCompletion\n      roleBoundItem\n      __typename\n    }\n    __typename\n  }\n}",
        }

    async def insert(
        self,
        response: Union[scrapy.http.Response, requests.Response],
    ) -> int:
        """Returns the number of rows written (new matches only)."""
        if response_status(response) != 200:
            raise FailedRequest()
        matches = response.json()["data"]["fetchPlayerMatchSummaries"]["matchSummaries"]
        versions = {version.value for version in GameVersion}
        rows = []
        for match in matches:
            # Only keep compatible game versions
            if match["version"] not in versions:
                logging.debug(
                    "Skipping match %s (version %s)", match["matchId"], match["version"]
                )
                continue
            rows.append(
                {
                    "match_id": str(match["matchId"]),
                    "match_creation_time": match["matchCreationTime"],
                    "match_duration_seconds": match["matchDuration"],
                    "queue_type": QueueType(match["queueType"]),
                    "region_id": Region(match["regionId"]),
                    "version": GameVersion(match["version"]),
                    "player_ids": [
                        make_player_id(
                            riot_user_name=player["riotUserName"],
                            riot_tag_line=player["riotTagLine"],
                        )
                        for player in match["teamA"] + match["teamB"]
                    ],
                }
            )
        if not rows:
            return 0
        stmt = insert(Match).on_conflict_do_nothing(index_elements=["match_id"])
        # Skipped (existing) matches aren't returned, see `UGGPlayer.insert`
        async with AsyncSessionLocal.begin() as session:
            written = await session.scalars(stmt.returning(Match.match_id), rows)
            return len(written.all())


class UGGMatchDetail:
    def __init__(
        self,
        region: Region,
        match_id: str,
        version: str,
        riot_user_name: str,
        riot_tag_line: str,
    ) -> None:
        self.riot_user_name = riot_user_name
        self.riot_tag_line = riot_tag_line
        self.match_id = match_id
        self.version = GameVersion(version)
        self.region = Region(region)

    def url(self) -> str:
        return str(
            urlunparse(
                URLComponents(
                    scheme="https",
                    netloc="u.gg",
                    path="/api",
                    params="",
                    query={},
                    fragment="",
                )
            )
        )

    def payload(
        self,
    ) -> dict[str, Any]:
        return {
            "operationName": "match",
            "variables": {
                "regionId": self.region.value,
                "riotUserName": self.riot_user_name,
                "riotTagLine": self.riot_tag_line,
                "matchId": str(self.match_id),
                "version": self.version.value,
            },
            "query": "query match($matchId: String!, $regionId: String!, $riotUserName: String!, $riotTagLine: String!, $version: String!) {\n  match(\n    matchId: $matchId\n    regionId: $regionId\n    riotUserName: $riotUserName\n    riotTagLine: $riotTagLine\n    version: $version\n  ) {\n    allPlayerRanks {\n      rankScores {\n        lastUpdatedAt\n        losses\n        lp\n        queueType\n        rank\n        role\n        seasonId\n        tier\n        wins\n        __typename\n      }\n      riotUserName\n      riotTagLine\n      __typename\n    }\n    historicalData {\n      kaDifferenceFrames {\n        oppValue\n        timestamp\n        youValue\n        __typename\n      }\n      xpDifferenceFrames {\n        oppValue\n        timestamp\n        youValue\n        __typename\n      }\n      teamOneOverview {\n        bans\n        baronKills\n        dragonKills\n        gold\n        inhibitorKills\n        kills\n        riftHeraldKills\n        towerKills\n        __typename\n      }\n      teamTwoOverview {\n        bans\n        baronKills\n        dragonKills\n        gold\n        inhibitorKills\n        kills\n        riftHeraldKills\n        towerKills\n        __typename\n      }\n      runes\n      skillPath\n      statShards\n      accountIdV3\n      csDifferenceFrames {\n        oppValue\n        timestamp\n        youValue\n        __typename\n      }\n      finishedItems {\n        itemId\n        timestamp\n        type\n        __typename\n      }\n      goldDifferenceFrames {\n        oppValue\n        timestamp\n        youValue\n        __typename\n      }\n      itemPath {\n        itemId\n        timestamp\n        type\n        __typename\n      }\n      matchId\n      metricsData {\n        cs\n        jungleCs\n        level\n        pid\n        position\n        riotTagLine\n        riotUserName\n        timestamp\n        totalDamageDoneToChampions\n        totalDamageTaken\n        totalGold\n        xp\n        __typename\n      }\n      postGameData {\n        assists\n        augments\n        carryPercentage\n        championId\n        cs\n        damage\n        damageTaken\n        deaths\n        gold\n        items\n        jungleCs\n        keystone\n        kills\n        level\n        role\n        subStyle\n        riotUserName\n        riotTagLine\n        summonerSpells\n        teamId\n        wardsPlaced\n        level\n        roleBoundItem\n        __typename\n      }\n      timelineData {\n        assistPids\n        assistRiotIds {\n          username\n          tagLine\n          __typename\n        }\n        buildingType\n        eventType\n        killerId\n        killerIds\n        laneType\n        monsterSubtype\n        monsterType\n        pid\n        position\n        riotTagLine\n        riotUserName\n        teamId\n        timestamp\n        towerType\n        victimId\n        victimRiotTagLine\n        victimRiotUserName\n        wardType\n        __typename\n      }\n      primaryStyle\n      queueType\n      regionId\n      subStyle\n      riotUserName\n      riotTagLine\n      __typename\n    }\n    matchSummary {\n      assists\n      augments\n      championId\n      cs\n      damage\n      deaths\n      gold\n      items\n      jungleCs\n      killParticipation\n      kills\n      level\n      matchCreationTime\n      matchDuration\n      matchId\n      maximumKillStreak\n      primaryStyle\n      queueType\n      regionId\n      role\n      runes\n      subStyle\n      summonerName\n      riotUserName\n      riotTagLine\n      summonerSpells\n      psHardCarry\n      psTeamPlay\n      lpInfo {\n        lp\n        placement\n        promoProgress\n        promoTarget\n        promotedTo {\n          tier\n          rank\n          __typename\n        }\n        __typename\n      }\n      teamA {\n        championId\n        summonerName\n        riotUserName\n        riotTagLine\n        teamId\n        role\n        hardCarry\n        teamplay\n        placement\n        playerSubteamId\n        __typename\n      }\n      teamB {\n        championId\n        summonerName\n        riotUserName\n        riotTagLine\n        teamId\n        role\n        hardCarry\n        teamplay\n        placement\n        playerSubteamId\n        __typename\n      }\n      version\n      visionScore\n      win\n      roleQuestCompletion\n      roleBoundItem\n      __typename\n    }\n    playerInfo {\n      accountIdV3\n      accountIdV4\n      exodiaUuid\n      iconId\n      puuidV4\n      regionId\n      summonerIdV3\n      summonerIdV4\n      summonerLevel\n      riotUserName\n      riotTagLine\n      __typename\n    }\n    performanceScore {\n      damageShare\n      damageShareAgg\n      damageShareTotal\n      finalLvlDiff\n      finalLvlDiffAgg\n      finalLvlDiffTotal\n      goldShare\n      goldShareAgg\n      goldShareTotal\n      hardCarry\n      killParticipation\n      killParticipationAgg\n      killParticipationTotal\n      kpOverGs\n      kpOverGsAgg\n      kpOverGsTotal\n      riotUserName\n      riotTagLine\n      teamplay\n      visionScore\n      visionScoreAgg\n      visionScoreTotal\n      __typename\n    }\n    winningTeam\n    __typename\n  }\n}",
        }

    async def insert(
        self, response: Union[scrapy.http.Response, requests.Response]
    ) -> dict[str, int]:
        if response_status(response) != 200:
            raise FailedRequest()
        match = response.json()["data"]["match"]
        summary = match["matchSummary"]
        history = match["historicalData"]
        match_id = str(summary["matchId"])
        player_id = make_player_id(
            riot_user_name=summary["riotUserName"],
            riot_tag_line=summary["riotTagLine"],
        )

        def is_player(x: dict[str, Any]) -> bool:
            return player_id == make_player_id(
                riot_user_name=x["riotUserName"], riot_tag_line=x["riotTagLine"]
            )

        def find_player(xs: list[dict[str, Any]], field: str) -> dict[str, Any]:
            for x in xs:
                if is_player(x):
                    return x
            raise ValueError(f"{player_id} not found in {field} of match {match_id}")

        post_game = find_player(history["postGameData"], "postGameData")
        performance = find_player(match["performanceScore"], "performanceScore")
        match_details = [
            {
                "match_id": match_id,
                "player_id": player_id,
                "team_id": make_team_id(post_game["teamId"]),
                "assists": summary["assists"],
                "augments": summary["augments"],
                "carry_percentage": post_game["carryPercentage"],
                "champion_id": summary["championId"],
                "cs": summary["cs"],
                # `matchSummary.damage` is 0, see `postGameData`
                "damage": post_game["damage"],
                "damage_taken": post_game["damageTaken"],
                "deaths": summary["deaths"],
                "gold": summary["gold"],
                "items": summary["items"],
                "jungle_cs": summary["jungleCs"],
                "keystone": post_game["keystone"],
                "kills": summary["kills"],
                "level": summary["level"],
                "role": summary["role"],
                "role_bound_item": summary["roleBoundItem"],
                "sub_style": summary["subStyle"],
                "wards_placed": post_game["wardsPlaced"],
                "maximum_kill_streak": summary["maximumKillStreak"],
                "primary_style": summary["primaryStyle"],
                "ps_hard_carry": summary["psHardCarry"],
                "ps_team_play": summary["psTeamPlay"],
                "role_quest_completion": summary["roleQuestCompletion"],
                "runes": summary["runes"],
                "vision_score": summary["visionScore"],
                "win": summary["win"],
                # `*Total` are the actual values, others are percentile scores
                "damage_share": performance["damageShareTotal"],
                "final_lvl_diff": performance["finalLvlDiffTotal"],
                "gold_share": performance["goldShareTotal"],
                "kill_participation": summary["killParticipation"],
                "skill_path": history["skillPath"],
                "stat_shards": history["statShards"],
                "summoner_spells": summary["summonerSpells"],
            }
        ]
        teams = [
            {
                "match_id": match_id,
                "team_id": team_id,
                "bans": team["bans"],
                "baron_kills": team["baronKills"],
                "dragon_kills": team["dragonKills"],
                "gold": team["gold"],
                "inhibitor_kills": team["inhibitorKills"],
                "kills": team["kills"],
                "rift_herald_kills": team["riftHeraldKills"],
                "tower_kills": team["towerKills"],
            }
            for team_id, team in (
                (TeamId.a, history["teamOneOverview"]),
                (TeamId.b, history["teamTwoOverview"]),
            )
        ]
        timeline_events = [
            {
                "match_id": match_id,
                "player_id": player_id,
                # index in the whole match's timeline, not just the player's
                "event_index": event_index,
                "team_id": (
                    make_team_id(event["teamId"])
                    if event["teamId"] is not None
                    else None
                ),
                "event_type": event["eventType"],
                "assist_ids": event["assistPids"],
                "assist_riot_ids": (
                    [
                        make_player_id(
                            riot_user_name=assist["username"],
                            riot_tag_line=assist["tagLine"],
                        )
                        for assist in event["assistRiotIds"]
                    ]
                    if event["assistRiotIds"] is not None
                    else None
                ),
                "building_type": event["buildingType"],
                "killer_id": event["killerId"],
                "killer_ids": event["killerIds"],
                "lane_type": event["laneType"],
                "monster_subtype": event["monsterSubtype"],
                "monster_type": event["monsterType"],
                "pid": event["pid"],
                **position_columns(event["position"]),
                "timestamp": event["timestamp"],
                "tower_type": event["towerType"],
                "victim_id": event["victimId"],
                # e.g. "Unknown Summoner" with an empty tag line
                "victim_player_id": (
                    make_player_id(
                        riot_user_name=event["victimRiotUserName"],
                        riot_tag_line=event["victimRiotTagLine"],
                    )
                    if event["victimRiotUserName"] and event["victimRiotTagLine"]
                    else None
                ),
                "ward_type": event["wardType"],
            }
            for event_index, event in enumerate(history["timelineData"])
            if is_player(event)
        ]
        stat_delta_events = [
            {
                "match_id": match_id,
                "player_id": player_id,
                "stat_type": stat_type,
                "opp_value": frame["oppValue"],
                "player_value": frame["youValue"],
                "timestamp": frame["timestamp"],
            }
            for stat_type, field in (
                (StatDelta.cs_difference, "csDifferenceFrames"),
                (StatDelta.ka_difference, "kaDifferenceFrames"),
                (StatDelta.gold_difference, "goldDifferenceFrames"),
                (StatDelta.xp_difference, "xpDifferenceFrames"),
            )
            for frame in history[field]
        ]
        metric_events = [
            {
                "match_id": match_id,
                "player_id": player_id,
                "cs": metric["cs"],
                "jungle_cs": metric["jungleCs"],
                "level": metric["level"],
                "pid": metric["pid"],
                **position_columns(metric["position"]),
                "timestamp": metric["timestamp"],
                "total_damage_done_to_champions": metric["totalDamageDoneToChampions"],
                "total_damage_taken": metric["totalDamageTaken"],
                "total_gold": metric["totalGold"],
                "xp": metric["xp"],
            }
            for metric in history["metricsData"]
            if is_player(metric)
        ]
        n_written = {}
        async with AsyncSessionLocal.begin() as session:
            for model, rows in (
                (MatchDetail, match_details),
                (Team, teams),
                (TimelineEvent, timeline_events),
                (StatDeltaEvent, stat_delta_events),
                (MetricEvent, metric_events),
            ):
                table = model.__table__
                if not rows:
                    n_written[table.name] = 0
                    continue
                stmt = (
                    insert(table)
                    .on_conflict_do_nothing()
                    .returning(*table.primary_key.columns)
                )
                n_written[table.name] = len((await session.execute(stmt, rows)).all())
        return n_written
