"""
uses declarative generated base class
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import (
    Mapped,
    MappedAsDataclass,
    DeclarativeBase,
    mapped_column,
)


class Base(DeclarativeBase):
    pass


class Leaderboard(Base, MappedAsDataclass):
    __tablename__ = "Leaderboard"

    iconId: Mapped[int]
    losses: Mapped[int]
    lp: Mapped[int]
    rank: Mapped[int]
    tier: Mapped[str]
    wins: Mapped[int]
    riotTagLine: Mapped[str] = mapped_column(primary_key=True)
    riotUserName: Mapped[str] = mapped_column(primary_key=True)
    create_date: Mapped[datetime] = mapped_column(insert_default=func.now())


class TimelineEvents(Base, MappedAsDataclass):
    __tablename__ = "TimelineEvents"

    matchId: Mapped[int] = mapped_column(primary_key=True)
    eventType: Mapped[str]  # TODO: restrict to `ward_placed`, `champion_killed`, etc.
    assistId: Mapped[Optional[str]]
    assistRiotIds: Mapped[Optional[list[str]]]
    buildingType: Mapped[Optional[str]]
    killerId: Mapped[Optional[str]]
    killerIds: Mapped[Optional[list[str]]]
    laneType: Mapped[str]  # TODO: notate exact lanes
    monsterSubtype: Mapped[Optional[str]]
    monsterType: Mapped[Optional[str]]
    pid: Mapped[int]
    position: Mapped[Optional[str]]
    riotTagLine: Mapped[str] = mapped_column(
        ForeignKey("PlayerData.riotTagLine"), ForeignKey("MatchData.riotTagLine")
    )
    riotUserName: Mapped[str] = mapped_column(
        ForeignKey("PlayerData.riotUserName"), ForeignKey("MatchData.riotUserName")
    )
    teamId: Mapped[Optional[str]]
    timestamp: Mapped[int]
    towerType: Mapped[Optional[str]]  # TODO: notate with tower types
    victimId: Mapped[Optional[str]]
    victimRiotTagLine: Mapped[Optional[str]] = mapped_column(
        ForeignKey("PlayerData.riotTagLine"), ForeignKey("MatchData.riotTagLine")
    )
    victimRiotUserName: Mapped[Optional[str]] = mapped_column(
        ForeignKey("PlayerData.riotTagLine"), ForeignKey("MatchData.riotTagLine")
    )
    wardType: Mapped[Optional[str]]


class StatDeltaEvents(Base, MappedAsDataclass):
    __tablename__ = "StatDeltaEvents"

    statType: Mapped[
        str
    ]  # TODO: annotate with `csDifference`, `kaDifference`, `xpDifference`, `goldDifference`
    oppValue: Mapped[int]
    playerValue: Mapped[int]
    timestamp: Mapped[int]
    riotUserName: Mapped[str] = mapped_column(primary_key=True)
    riotTagLine: Mapped[str] = mapped_column(primary_key=True)


class PlayerData(Base, MappedAsDataclass):
    __tablename__ = "PlayerData"

    assists: Mapped[int]
    augments: Mapped[list[int]]
    carryPercentage: Mapped[float]
    championId: Mapped[int]
    cs: Mapped[int]
    damage: Mapped[int]
    damageTaken: Mapped[int]
    deaths: Mapped[int]
    gold: Mapped[int]
    items: Mapped[list[int]]
    jungleCs: Mapped[int]
    keystone: Mapped[int]
    kills: Mapped[int]
    level: Mapped[int]
    riotTagLine: Mapped[str] = mapped_column(primary_key=True)
    riotUserName: Mapped[str] = mapped_column(primary_key=True)
    matchId: Mapped[int] = mapped_column(ForeignKey("MatchData.matchId"))
    role: Mapped[int]
    roleBoundItem: Mapped[int]
    subStyle: Mapped[int]
    summonerSpells: Mapped[list[int]]
    teamId: Mapped[int]
    wardsPlaced: Mapped[int]
    wardsPlaced: Mapped[int]
    maximumKillStreak: Mapped[int]
    primaryStyle: Mapped[int]
    psHardCarry: Mapped[int]
    psTeamPlay: Mapped[int]
    roleQuestCompletion: Mapped[int]
    runes: Mapped[list[int]]
    visionScore: Mapped[int]
    win: Mapped[bool]
    damageShare: Mapped[float]
    finalLvlDiff: Mapped[int]
    goldShare: Mapped[float]
    killParticipation: Mapped[float]
    skillPath: Mapped[list[int]]
    statShards: Mapped[list[int]]


class MatchData(Base, MappedAsDataclass):
    __tablename__ = "MatchData"

    matchCreationTime: Mapped[int]
    matchDurationSeconds: Mapped[int]
    matchId: Mapped[int] = mapped_column(primary_key=True, ForeignKey("PlayerData.matchId"), ForeignKey("TimelineEvents.matchId"))
    queueType: Mapped[str]  # enum
    regionId: Mapped[str]  # should be enum
    version: Mapped[str]  # enum
    wTeamBans: Mapped[list[int]]
    wTeamBaronKills: Mapped[list[int]]
    wTeamDragonKills: Mapped[list[int]]
    wTeamGold: Mapped[int]
    wTeamInhibitorKills: Mapped[int]
    wTeamRiftHeraldKills: Mapped[int]
    wTeamTowerKills: Mapped[int]
    wTeamTeamId: Mapped[int]
    lTeamBans: Mapped[list[int]]
    lTeamBaronKills: Mapped[list[int]]
    lTeamDragonKills: Mapped[list[int]]
    lTeamGold: Mapped[int]
    lTeamInhibitorKills: Mapped[int]
    lTeamRiftHeraldKills: Mapped[int]
    lTeamTowerKills: Mapped[int]
    lTeamTeamId: Mapped[int]
