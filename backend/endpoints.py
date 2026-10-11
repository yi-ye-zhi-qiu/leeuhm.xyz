"""Main interface for bronze data, requests/Scrapy are just busses."""

import os
import psycopg2
from collections import namedtuple
from typing import Any, Literal, Optional
from urllib.parse import urlunparse
from dataclasses import dataclass

from scrapy.http import Response

from backend.models import Leaderboard, MatchData, PlayerData

QUEUE_TYPE = 420  # 5v5 Summoner's rift
SEASON_IDS = [25, 26]  # Most recent (31-Aug-2026 2 seasons)
Region = Literal["na", "euw", "kr"]

URLComponents = namedtuple(
    typename="URLComponents",
    field_names=["scheme", "netloc", "path", "params", "query", "fragment"],
)  # builder pattern


class UGGLeaderboard:
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
                "regionId": region,
            },
            "query": "query getRankedLeaderboard($page: Int, $queueType: Int, $regionId: String!) {\n  leaderboardPage(page: $page, queueType: $queueType, regionId: $regionId) {\n    totalPlayerCount\n    topPlayerMostPlayedChamp\n    players {\n      iconId\n      losses\n      lp\n      overallRanking\n      rank\n      summonerLevel\n      riotTagLine\n      riotUserName\n      tier\n      wins\n      __typename\n    }\n    __typename\n  }\n}",
        }

    def insert(response: Response) -> None:
        players = response.json()["data"]["leaderboardPage"]["players"]
        logger.info("Found %d players on page %d", len(players), page_index)
        item: Leaderboard = ...
        connection = psycopg2.connect(os.environ["DATABASE_URL"])
        connection.autocommit = True
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO "Leaderboard" VALUES (
                %(iconId)d
                , %(losses)d
                , %(lp)d
                , %(rank)d
                , %(riotTagLine)s
                , %(riotUserName)s
                , %(summonerLevel)d
                , %(tier)s
                , %(wins)d
                -- Populate as current timestamp
                , %(current_timestamp)s
            )
            ON CONFLICT DO UPDATE
            """,
            item,
        )
        return


class UGGMatchSummary:
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
                "regionId": region,
                "riotUserName": riot_user_name,
                "riotTagLine": riot_tag_line,
                "queueType": [],
                "duoRiotUserName": "",
                "duoRiotTagLine": "",
                "role": [],
                "seasonIds": SEASON_IDS,
                "championId": [],
                "page": page_index,
            },
            "query": "query FetchMatchSummaries($championId: [Int], $page: Int, $queueType: [Int], $duoRiotUserName: String, $duoRiotTagLine: String, $regionId: String!, $role: [Int], $seasonIds: [Int]!, $riotUserName: String!, $riotTagLine: String!) {\n  fetchPlayerMatchSummaries(\n    championId: $championId\n    page: $page\n    queueType: $queueType\n    duoRiotUserName: $duoRiotUserName\n    duoRiotTagLine: $duoRiotTagLine\n    regionId: $regionId\n    role: $role\n    seasonIds: $seasonIds\n    riotUserName: $riotUserName\n    riotTagLine: $riotTagLine\n  ) {\n    finishedMatchSummaries\n    totalNumMatches\n    matchSummaries {\n      assists\n      augments\n      championId\n      cs\n      damage\n      deaths\n      gold\n      items\n      jungleCs\n      killParticipation\n      kills\n      level\n      matchCreationTime\n      matchDuration\n      matchId\n      maximumKillStreak\n      primaryStyle\n      queueType\n      regionId\n      role\n      runes\n      subStyle\n      summonerName\n      riotUserName\n      riotTagLine\n      summonerSpells\n      psHardCarry\n      psTeamPlay\n      lpInfo {\n        lp\n        placement\n        promoProgress\n        promoTarget\n        promotedTo {\n          tier\n          rank\n          __typename\n        }\n        __typename\n      }\n      teamA {\n        championId\n        summonerName\n        riotUserName\n        riotTagLine\n        teamId\n        role\n        hardCarry\n        teamplay\n        placement\n        playerSubteamId\n        __typename\n      }\n      teamB {\n        championId\n        summonerName\n        riotUserName\n        riotTagLine\n        teamId\n        role\n        hardCarry\n        teamplay\n        placement\n        playerSubteamId\n        __typename\n      }\n      version\n      visionScore\n      win\n      roleQuestCompletion\n      roleBoundItem\n      __typename\n    }\n    __typename\n  }\n}",
        }

    def insert(response: Response) -> None:
        games = response.json()["data"]["fetchPlayerMatchSummaries"]["matchSummaries"]
        logger.info("Found %d matches for %s", len(games), riot_user_name)
        item: MatchData = ...
        connection = psycopg2.connect(os.environ["DATABASE_URL"])
        connection.autocommit = True
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO "MatchData" VALUES (
                %(matchCreationTime)d
                , %(matchDurationSeconds)d
                , %(matchId)d
                , %(queueType)s
                , %(regionId)s
                , %(version)s
                , %(winningTeam)d
            )
            ON CONFLICT DO NOTHING
            """,
            item,
        )


class UGGMatchDetail:
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
        region: Region,
        riot_user_name: str,
        riot_tag_line: str,
        match_id: str,
        version: str,
    ) -> dict[str, Any]:
        return {
            "operationName": "match",
            "variables": {
                "regionId": region,
                "riotUserName": riot_user_name,
                "riotTagLine": riot_tag_line,
                "matchId": str(match_id),
                "version": version,
            },
            "query": "query match($matchId: String!, $regionId: String!, $riotUserName: String!, $riotTagLine: String!, $version: String!) {\n  match(\n    matchId: $matchId\n    regionId: $regionId\n    riotUserName: $riotUserName\n    riotTagLine: $riotTagLine\n    version: $version\n  ) {\n    allPlayerRanks {\n      rankScores {\n        lastUpdatedAt\n        losses\n        lp\n        queueType\n        rank\n        role\n        seasonId\n        tier\n        wins\n        __typename\n      }\n      riotUserName\n      riotTagLine\n      __typename\n    }\n    historicalData {\n      kaDifferenceFrames {\n        oppValue\n        timestamp\n        youValue\n        __typename\n      }\n      xpDifferenceFrames {\n        oppValue\n        timestamp\n        youValue\n        __typename\n      }\n      teamOneOverview {\n        bans\n        baronKills\n        dragonKills\n        gold\n        inhibitorKills\n        kills\n        riftHeraldKills\n        towerKills\n        __typename\n      }\n      teamTwoOverview {\n        bans\n        baronKills\n        dragonKills\n        gold\n        inhibitorKills\n        kills\n        riftHeraldKills\n        towerKills\n        __typename\n      }\n      runes\n      skillPath\n      statShards\n      accountIdV3\n      csDifferenceFrames {\n        oppValue\n        timestamp\n        youValue\n        __typename\n      }\n      finishedItems {\n        itemId\n        timestamp\n        type\n        __typename\n      }\n      goldDifferenceFrames {\n        oppValue\n        timestamp\n        youValue\n        __typename\n      }\n      itemPath {\n        itemId\n        timestamp\n        type\n        __typename\n      }\n      matchId\n      metricsData {\n        cs\n        jungleCs\n        level\n        pid\n        position\n        riotTagLine\n        riotUserName\n        timestamp\n        totalDamageDoneToChampions\n        totalDamageTaken\n        totalGold\n        xp\n        __typename\n      }\n      postGameData {\n        assists\n        augments\n        carryPercentage\n        championId\n        cs\n        damage\n        damageTaken\n        deaths\n        gold\n        items\n        jungleCs\n        keystone\n        kills\n        level\n        role\n        subStyle\n        riotUserName\n        riotTagLine\n        summonerSpells\n        teamId\n        wardsPlaced\n        level\n        roleBoundItem\n        __typename\n      }\n      timelineData {\n        assistPids\n        assistRiotIds {\n          username\n          tagLine\n          __typename\n        }\n        buildingType\n        eventType\n        killerId\n        killerIds\n        laneType\n        monsterSubtype\n        monsterType\n        pid\n        position\n        riotTagLine\n        riotUserName\n        teamId\n        timestamp\n        towerType\n        victimId\n        victimRiotTagLine\n        victimRiotUserName\n        wardType\n        __typename\n      }\n      primaryStyle\n      queueType\n      regionId\n      subStyle\n      riotUserName\n      riotTagLine\n      __typename\n    }\n    matchSummary {\n      assists\n      augments\n      championId\n      cs\n      damage\n      deaths\n      gold\n      items\n      jungleCs\n      killParticipation\n      kills\n      level\n      matchCreationTime\n      matchDuration\n      matchId\n      maximumKillStreak\n      primaryStyle\n      queueType\n      regionId\n      role\n      runes\n      subStyle\n      summonerName\n      riotUserName\n      riotTagLine\n      summonerSpells\n      psHardCarry\n      psTeamPlay\n      lpInfo {\n        lp\n        placement\n        promoProgress\n        promoTarget\n        promotedTo {\n          tier\n          rank\n          __typename\n        }\n        __typename\n      }\n      teamA {\n        championId\n        summonerName\n        riotUserName\n        riotTagLine\n        teamId\n        role\n        hardCarry\n        teamplay\n        placement\n        playerSubteamId\n        __typename\n      }\n      teamB {\n        championId\n        summonerName\n        riotUserName\n        riotTagLine\n        teamId\n        role\n        hardCarry\n        teamplay\n        placement\n        playerSubteamId\n        __typename\n      }\n      version\n      visionScore\n      win\n      roleQuestCompletion\n      roleBoundItem\n      __typename\n    }\n    playerInfo {\n      accountIdV3\n      accountIdV4\n      exodiaUuid\n      iconId\n      puuidV4\n      regionId\n      summonerIdV3\n      summonerIdV4\n      summonerLevel\n      riotUserName\n      riotTagLine\n      __typename\n    }\n    performanceScore {\n      damageShare\n      damageShareAgg\n      damageShareTotal\n      finalLvlDiff\n      finalLvlDiffAgg\n      finalLvlDiffTotal\n      goldShare\n      goldShareAgg\n      goldShareTotal\n      hardCarry\n      killParticipation\n      killParticipationAgg\n      killParticipationTotal\n      kpOverGs\n      kpOverGsAgg\n      kpOverGsTotal\n      riotUserName\n      riotTagLine\n      teamplay\n      visionScore\n      visionScoreAgg\n      visionScoreTotal\n      __typename\n    }\n    winningTeam\n    __typename\n  }\n}",
        }

    def insert(response: Response) -> None:
        # TODO: parse data
        item: PlayerData = ...
        connection = psycopg2.connect(os.environ["DATABASE_URL"])
        connection.autocommit = True
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO "PlayerData" VALUES (
                %(assists)d
                , %(augments)d
                , %(carryPercentage)d
                , %(championId)d
                , %(cs)d
                , %(damage)d
                , %(damageTaken)d
                , %(detahs)d
                , %(gold)d
                , %(items)d
                , %(jungleCs)d
                , %(keystone)d
                , %(kills)d
                , %(level)d
                , %(riotTagLine)s
                , %(riotUserName)s
                , %(role)d
                , %(roleBoundItem)d
                , %(subStyle)d
                , %(summonerSpells)d
                , %(teamId)d
                , %(wardsPlaced)d
                , %(maximumKillStreak)d
                , %(primaryStyle)d
                , %(psHardCarry)d
                , %(psTeamPlay)d
                , %(roleQuestCompletion)d
                , %(runes)d
                , %(visionScore)d
                , %(win)d
                , %(damageShare)d
                , %(finalLvlDiff)d
                , %(goldShare)d
                , %(killParticipation)d
                , %(skillPath)d
                , %(statShards)d
                , %(timelineEvents)d
                , %(statDeltas)d
            )
            """,
            item,
        )


class UGGAdapter:
    pass
