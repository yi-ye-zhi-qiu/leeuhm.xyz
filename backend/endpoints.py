"""Main interface for bronze data, requests/Scrapy are just busses."""

from datetime import time
import os
from alembic.context import execute
import scrapy.http
import logging
import requests
import psycopg2
from typing import Any, Literal, Union
from collections import namedtuple
from urllib.parse import urlunparse

from sqlalchemy import insert
from sqlalchemy.sql.functions import now

from .db import execute_statement
from .exceptions import FailedRequest
from .models import MetricEvent, Player, Match, MatchDetail, Region, StatDeltaEvent, Team, TeamId, TimelineEvent, make_player_id, make_team_id

QUEUE_TYPE = 420  # 5v5 Summoner's rift
SEASON_IDS = [25, 26]  # Most recent (31-Aug-2026 2 seasons)

URLComponents = namedtuple(
    typename="URLComponents",
    field_names=["scheme", "netloc", "path", "params", "query", "fragment"],
)  # builder pattern


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
                "regionId": region,
            },
            "query": "query getRankedLeaderboard($page: Int, $queueType: Int, $regionId: String!) {\n  leaderboardPage(page: $page, queueType: $queueType, regionId: $regionId) {\n    totalPlayerCount\n    topPlayerMostPlayedChamp\n    players {\n      iconId\n      losses\n      lp\n      overallRanking\n      rank\n      summonerLevel\n      riotTagLine\n      riotUserName\n      tier\n      wins\n      __typename\n    }\n    __typename\n  }\n}",
        }

    def insert(
        self, response: Union[scrapy.http.Response, requests.Response], page_index: int
    ) -> None:
        if type(response) not in (scrapy.http.Response, requests.Response):
            raise TypeError()
        if type(response) == scrapy.http.Response:
            status = response.status
        if type(response) == requests.Response:
            status = response.status_code
        if status != 200:
            raise FailedRequest()
        players = response.json()["data"]["leaderboardPage"]["players"]
        logging.info("Found %d players on %d", len(players), page_index)
        for player in players:
            stmt = (
                insert(Player)
                .values(
                    icon_id=player["iconId"],
                    losses=int(player["losses"]),
                    lp=str(player["lp"]),
                    rank=player["rank"].lower(),
                    tier=player["tier"].lower(),
                    wins=player["wins"],
                    player_id=make_player_id(
                        riot_user_name=player["riot_user_name"],
                        riot_tag_line=player["riot_tag_line"],
                    ),
                    riot_tag_line=player["riot_tag_line"],
                    riot_user_name=player["riot_user_name"],
                    summoner_level=player["summonerLevel"],
                    crawl_timestamp=now(),
                )
                # Player is a latest table
                .on_conflict_do_update(index_elements=["player_id"])
            )
            execute_statement(stmt)


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

    def insert(
        self,
        response: Union[scrapy.http.Response, requests.Response],
    ) -> None:
        if type(response) not in (scrapy.http.Response, requests.Response):
            raise TypeError()
        if type(response) == scrapy.http.Response:
            status = response.status
        if type(response) == requests.Response:
            status = response.status_code
        if status != 200:
            raise FailedRequest()
        matches = response.json()["data"]["fetchPlayerMatchSummaries"]["matchSummaries"]
        for match in matches:
            player_ids: list[Player.player_id] = []
            for player in match["teamA"] + match["teamB"]:
                player_ids.append(
                    make_player_id(
                        riot_user_name=player["riot_user_name"],
                        riot_tag_line=player["riot_tag_line"],
                    )
                )
            stmt = (
                insert(Match)
                .values(
                    match_creation_time=match["matchCreationTime"],
                    match_duration_seconds=match["matchDuration"],
                    match_id=match["matchId"],
                    team_ids=["100", "200"],
                    player_ids=player_ids,
                    queue_type=match["queueType"],
                    region_id=match["regionId"],
                    version=match["version"],
                )
            )
            execute_statement(stmt)


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
        self.version = version
        self.region = Region

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
                "regionId": self.region,
                "riotUserName": self.riot_user_name,
                "riotTagLine": self.riot_tag_line,
                "matchId": str(self.match_id),
                "version": self.version,
            },
            "query": "query match($matchId: String!, $regionId: String!, $riotUserName: String!, $riotTagLine: String!, $version: String!) {\n  match(\n    matchId: $matchId\n    regionId: $regionId\n    riotUserName: $riotUserName\n    riotTagLine: $riotTagLine\n    version: $version\n  ) {\n    allPlayerRanks {\n      rankScores {\n        lastUpdatedAt\n        losses\n        lp\n        queueType\n        rank\n        role\n        seasonId\n        tier\n        wins\n        __typename\n      }\n      riotUserName\n      riotTagLine\n      __typename\n    }\n    historicalData {\n      kaDifferenceFrames {\n        oppValue\n        timestamp\n        youValue\n        __typename\n      }\n      xpDifferenceFrames {\n        oppValue\n        timestamp\n        youValue\n        __typename\n      }\n      teamOneOverview {\n        bans\n        baronKills\n        dragonKills\n        gold\n        inhibitorKills\n        kills\n        riftHeraldKills\n        towerKills\n        __typename\n      }\n      teamTwoOverview {\n        bans\n        baronKills\n        dragonKills\n        gold\n        inhibitorKills\n        kills\n        riftHeraldKills\n        towerKills\n        __typename\n      }\n      runes\n      skillPath\n      statShards\n      accountIdV3\n      csDifferenceFrames {\n        oppValue\n        timestamp\n        youValue\n        __typename\n      }\n      finishedItems {\n        itemId\n        timestamp\n        type\n        __typename\n      }\n      goldDifferenceFrames {\n        oppValue\n        timestamp\n        youValue\n        __typename\n      }\n      itemPath {\n        itemId\n        timestamp\n        type\n        __typename\n      }\n      matchId\n      metricsData {\n        cs\n        jungleCs\n        level\n        pid\n        position\n        riotTagLine\n        riotUserName\n        timestamp\n        totalDamageDoneToChampions\n        totalDamageTaken\n        totalGold\n        xp\n        __typename\n      }\n      postGameData {\n        assists\n        augments\n        carryPercentage\n        championId\n        cs\n        damage\n        damageTaken\n        deaths\n        gold\n        items\n        jungleCs\n        keystone\n        kills\n        level\n        role\n        subStyle\n        riotUserName\n        riotTagLine\n        summonerSpells\n        teamId\n        wardsPlaced\n        level\n        roleBoundItem\n        __typename\n      }\n      timelineData {\n        assistPids\n        assistRiotIds {\n          username\n          tagLine\n          __typename\n        }\n        buildingType\n        eventType\n        killerId\n        killerIds\n        laneType\n        monsterSubtype\n        monsterType\n        pid\n        position\n        riotTagLine\n        riotUserName\n        teamId\n        timestamp\n        towerType\n        victimId\n        victimRiotTagLine\n        victimRiotUserName\n        wardType\n        __typename\n      }\n      primaryStyle\n      queueType\n      regionId\n      subStyle\n      riotUserName\n      riotTagLine\n      __typename\n    }\n    matchSummary {\n      assists\n      augments\n      championId\n      cs\n      damage\n      deaths\n      gold\n      items\n      jungleCs\n      killParticipation\n      kills\n      level\n      matchCreationTime\n      matchDuration\n      matchId\n      maximumKillStreak\n      primaryStyle\n      queueType\n      regionId\n      role\n      runes\n      subStyle\n      summonerName\n      riotUserName\n      riotTagLine\n      summonerSpells\n      psHardCarry\n      psTeamPlay\n      lpInfo {\n        lp\n        placement\n        promoProgress\n        promoTarget\n        promotedTo {\n          tier\n          rank\n          __typename\n        }\n        __typename\n      }\n      teamA {\n        championId\n        summonerName\n        riotUserName\n        riotTagLine\n        teamId\n        role\n        hardCarry\n        teamplay\n        placement\n        playerSubteamId\n        __typename\n      }\n      teamB {\n        championId\n        summonerName\n        riotUserName\n        riotTagLine\n        teamId\n        role\n        hardCarry\n        teamplay\n        placement\n        playerSubteamId\n        __typename\n      }\n      version\n      visionScore\n      win\n      roleQuestCompletion\n      roleBoundItem\n      __typename\n    }\n    playerInfo {\n      accountIdV3\n      accountIdV4\n      exodiaUuid\n      iconId\n      puuidV4\n      regionId\n      summonerIdV3\n      summonerIdV4\n      summonerLevel\n      riotUserName\n      riotTagLine\n      __typename\n    }\n    performanceScore {\n      damageShare\n      damageShareAgg\n      damageShareTotal\n      finalLvlDiff\n      finalLvlDiffAgg\n      finalLvlDiffTotal\n      goldShare\n      goldShareAgg\n      goldShareTotal\n      hardCarry\n      killParticipation\n      killParticipationAgg\n      killParticipationTotal\n      kpOverGs\n      kpOverGsAgg\n      kpOverGsTotal\n      riotUserName\n      riotTagLine\n      teamplay\n      visionScore\n      visionScoreAgg\n      visionScoreTotal\n      __typename\n    }\n    winningTeam\n    __typename\n  }\n}",
        }

    def insert(self, response: Union[scrapy.http.Response, requests.Response]) -> None:
        if type(response) not in (scrapy.http.Response, requests.Response):
            raise TypeError()
        if type(response) == scrapy.http.Response:
            status = response.status
        if type(response) == requests.Response:
            status = response.status_code
        if status != 200:
            raise FailedRequest()
        data = response.json()["data"]["match"]
        summary = data["matchSummary"]
        performance = [
            x["performanceScore"]
            for x in data["performanceScore"]
            if (
                x["riotUserName"] == self.riot_user_name
                and x["riotTagLine"] == self.riot_tag_line
            )
        ]
        post_game_data = [
            x
            for x in data["historicalData"]["postGameData"]
            if (
                x["riotUserName"] == self.riot_user_name
                and x["riotTagLine"] == self.riot_tag_line
            )
        ]
        stmt = insert(MatchDetail).values(
            assists=summary["assists"],
            augments=summary["augments"],
            champion_id=summary["championId"],
            cs=summary["cs"],
            damage=post_game_data["damage"],
            deaths=summary["deaths"],
            gold=summary["gold"],
            items=summary["items"],
            jungle_cs=summary["jungle_cs"],
            kill_participation=summary["killParticipation"],
            kills=summary["kills"],
            level=summary["level"],
            maximum_kill_streak=summary["maximumKillStreak"],
            primary_style=summary["primaryStyle"],
            ps_hard_carry=summary["psHardCarry"],
            ps_team_play=summary["psTeamPlay"],
            role=summary["role"],
            role_bound_item=summary["roleBoundItem"],
            role_quest_compleition=summary["role_quest_completion"],
            sub_style=summary["subStyle"],
            runes=summary["runes"],
            win=summary["win"],
            vision_score=summary["vision_score"],
            damage_share=performance["damageShareTotal"],
            final_lvl_diff=performance["finalLvlDiff"],
            gold_share=performance["goldShare"],
            match_id=summary["matchId"],
            player_id=make_player_id(
                riot_tag_line=summary["riotTagLine"],
                riot_user_name=summary["riotUserName"],
            ),
            skill_path=data["historicalData"]["skillPath"],
            stat_shareds=data["historicalData"]["statShards"],
            summoner_spells=summary["summonerSpells"]
        )
        execute_statement(stmt)
        for timeline_event in data["historicalData"]["timelineData"]:
            stmt = insert(TimelineEvent).values(
                match_id=summary["matchId"],
                player_id=make_player_id(
                    riot_tag_line=summary["riotTagLine"],
                    riot_user_name=summary["riotUserName"]
                ),
                team_id=make_team_id(timeline_event["teamId"]),
                event_type=timeline_event["eventType"],
                assist_id=timeline_event["assistPids"],
                assist_riot_ids=timeline_event=timeline_event["assistRiotIds"],
                building_type=timeline_event["buildingType"],
                killer_id=timeline_event["killerId"],
                killer_ids=timeline_event["killerIds"],
                lane_type=timeline_event["laneType"],
                monster_subtype=timeline_eent["monsterSubtype"],
                monster_type=timeline_event["monsterType"],
                pid=timeline_event["pid"],
                position=timeline_event["position"],
                timestamp=timeline_event["timestamp"],
                tower_type=timeline_event["towerType"],
                victim_id=timeline_event["victimId"],
                victim_player_id=make_player_id(
                    riot_tag_line=timeline_event["victimRiotTagLine"],
                    riot_user_name=timeline_event["victimRiotUserName"]
                ),
                ward_type=timeline_event["wardType"],
            )
            execute_statement(stmt)
        for stat_type, stat_delta in [
            ("cs_difference", data["historicalData"]["csDifferenceFrames"]),
            ("ka_difference", data["historicalData"]["kaDifferenceFrames"]),
            ("gold_difference", data["historicalData"]["goldDifferenceFrames"]),
            ("xp_difference", data["historicalData"]["xpDifferenceFrames"])
        ]:
            stmt = insert(StatDeltaEvent).values(
                stat_type=stat_type,
                opp_value=stat_delta["oppValue"],
                player_value=stat_delta["youValue"],
                timestamp=stat_delta["timestamp"],
                player_id=make_player_id(
                    riot_tag_line=summary["riotTagLine"],
                    riot_user_name=summary["riotUserName"]
                ),
                match_id=summary["matchId"]
            )
            execute_statement(stmt)
        for metric_event in data["historicalData"]["metricsData"]:
            stmt = insert(MetricEvent).values(
                cs=metric_event["cs"],
                jungle_cs=metric_event["jungleCs"],
                level=metric_event["level"],
                pid=metric_event["pid"],
                position=metric_event["position"],
                player_id=make_player_id(
                    riot_tag_line=metric_event["riotTagLine"],
                    riot_user_name=metric_event["riotUserName"]
                ),
                timestamp=metric_event["timestamp"],
                total_damage_done_to_champions=metric_event["totalDamageDoneToChampions"],
                total_damage_taken=metric_event["total_damage_taken"],
                total_gold=metric_event["totalGold"],
                xp=metric_event["xp"]
            )
            execute_statement(stmt)
        team_a = data["historicalData"]["teamOneOverview"]
        team_a["teamId"] = TeamId.a
        team_b = data["historicalData"]["teamTwoOverview"]
        team_b["teamId"] = TeamId.b
        teams = [team_a, team_b]
        for team_data in teams:
            stmt = insert(Team).values(
                team_id=team_data["teamId"],
                baron_kills=team_data["baronKills"],
                dragon_kills=team_data["dragonKills"],
                gold=team_data["gold"],
                inhibitor_kills=team_data["inhibitorKills"],
                kills=team_data["kills"],
                rift_herald_kills=team_data["riftHeraldKills"],
                tower_kills=team_data["towerKillss"],
            )
            execute_statement(stmt)
