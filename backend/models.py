"""Annontated declarative table configuration of leeuhm.xyz."""

import enum
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
from sqlalchemy import (
    ARRAY,
    BIGINT,
    TIMESTAMP,
    ForeignKey,
    ForeignKeyConstraint,
    MetaData,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import (
    Mapped,
    MappedAsDataclass,
    DeclarativeBase,
    composite,
    mapped_column,
    relationship,
)

metadata_obj = MetaData(
    # PostgreSQL has a limit of 63 characters
    naming_convention={"uq": "uq_%(table_name)s_%(column_0_N_name)s"}
)


# League of legends is available in north america ("na"),
# EU West ("euw"), Korea ("kr"). These are shorthands for server
# regions and is, at the moment, non extensive (I think there's
# EU West 2 or something...).
class Region(enum.Enum):
    na = "na1"
    euw = "euw"
    kr = "kr"


class TeamId(enum.Enum):
    a = "a"
    b = "b"


# League of Legends' matches consist of 2 teams.
def make_team_id(team_id: str) -> TeamId:
    return {100: TeamId.a, 200: TeamId.b}[int(team_id)]


# League of Legends' matches are of a few types.
class QueueType(enum.Enum):
    ranked_solo_5x5 = "ranked_solo_5x5"


# Compatible, desired game versions.
class GameVersion(enum.Enum):
    _16_20 = "16_20"
    _16_19 = "16_19"
    _16_18 = "16_18"
    _16_17 = "16_17"
    _16_16 = "16_16"
    _16_15 = "16_15"
    _16_14 = "16_14"
    _16_13 = "16_13"
    _16_12 = "16_12"
    _16_11 = "16_11"
    _16_10 = "16_10"
    _16_09 = "16_09"
    _16_08 = "16_08"
    _16_07 = "16_07"
    _16_06 = "16_06"
    _16_05 = "16_05"
    _16_04 = "16_04"
    _16_03 = "16_03"
    _16_02 = "16_02"
    _16_01 = "16_01"
    # Older than this are out-of-scope for now (>1 year ago),
    # since they involve breaking changes to game mechanics,
    # i.e. Attakhan.


# This will define a Python object model & database metadata. We start by subclassing
# `DeclarativeBase`, and customizing our type annotation map between Python types and SQL types.
# https://docs.sqlalchemy.org/en/21/orm/quickstart.html
# https://docs.sqlalchemy.org/en/21/orm/declarative_tables.html#customizing-the-type-map
# We integrate data classes in order to reuse these schemas in bronze
# ETL processes.
class Base(MappedAsDataclass, DeclarativeBase):
    metadata = metadata_obj
    type_annotation_map = {
        int: BIGINT,
        datetime: TIMESTAMP(timezone=True),
        str: String(),
        list[int]: ARRAY(BIGINT),
        list[str]: ARRAY(String()),
    }


class Rank(enum.Enum):
    i = "i"
    ii = "ii"
    iii = "iii"
    iv = "iv"
    v = "v"


class Tier(enum.Enum):
    challenger = "challenger"
    grand_master = "grandmaster"
    master = "master"
    diamond = "diamond"
    emerald = "emerald"
    platinum = "platinum"
    gold = "gold"
    silver = "silver"
    bronze = "bronze"
    iron = "iron"


def make_player_id(*args, riot_user_name: str, riot_tag_line: str):
    return f"{riot_user_name}#{riot_tag_line}"


class Player(Base):
    __tablename__ = "player"

    icon_id: Mapped[int]
    losses: Mapped[int]
    lp: Mapped[Optional[int]]
    rank: Mapped[Optional[Rank]]
    tier: Mapped[Optional[Tier]]
    wins: Mapped[int]
    summoner_level: Mapped[int]
    region: Mapped[Region]
    # NOTE: A player's data can change over time. This table is just latest
    # and is not snapshotted.
    updated_at: Mapped[datetime] = mapped_column(
        insert_default=func.now(), onupdate=func.now(), init=False
    )
    player_id: Mapped[str] = mapped_column(primary_key=True)
    # Riot, the company who owns League of Legends, tends to split `player_id`
    # into both a tag line (like #na1) and a user name. This determines uniqueness
    # and is what allows the same user name across multiple tags, or regions.
    riot_tag_line: Mapped[str]
    riot_user_name: Mapped[str]

    def __repr__(self) -> str:
        return f"Player(player_id={self.player_id!r})"


@dataclass
class Position:  # e.g. [{x: 603, y: 611}]
    x: Optional[int]
    y: Optional[int]


class TimelineEvent(Base):
    __tablename__ = "timeline_event"
    __table_args__ = (
        ForeignKeyConstraint(
            ["match_id", "player_id"],
            ["match_detail.match_id", "match_detail.player_id"],
        ),
    )

    match_id: Mapped[str] = mapped_column(primary_key=True)
    player_id: Mapped[str] = mapped_column(primary_key=True)
    team_id: Mapped[Optional[TeamId]] = mapped_column(nullable=True)
    event_type: Mapped[str]  # TODO: restrict to `ward_placed`, `champion_killed`, etc.
    assist_id: Mapped[Optional[int]]
    assist_riot_ids: Mapped[Optional[list[str]]]
    building_type: Mapped[Optional[str]]
    killer_id: Mapped[Optional[str]]
    killer_ids: Mapped[Optional[list[str]]]
    lane_type: Mapped[str]  # TODO: notate exact lanes
    monster_subtype: Mapped[Optional[str]]
    monster_type: Mapped[Optional[str]]
    pid: Mapped[int]
    position: Mapped[Position] = composite(
        mapped_column("position_x", nullable=True),
        mapped_column("position_y", nullable=True),
    )
    timestamp: Mapped[int] = mapped_column(primary_key=True)
    tower_type: Mapped[Optional[str]]  # TODO: notate with tower types
    victim_id: Mapped[Optional[str]]
    victim_player_id: Mapped[Optional[str]]
    ward_type: Mapped[Optional[str]]

    def __repr__(self) -> str:
        return (
            f"TimelineEvent(player_id={self.player_id!r}, match_id={self.match_id!r})"
        )


class StatDelta(enum.Enum):
    cs_difference = "cs_difference"
    ka_difference = "ka_difference"
    xp_difference = "xp_difference"
    gold_difference = "gold_difference"


class StatDeltaEvent(Base):
    __tablename__ = "stat_delta_event"
    __table_args__ = (
        ForeignKeyConstraint(
            ["match_id", "player_id"],
            ["match_detail.match_id", "match_detail.player_id"],
        ),
    )

    stat_type: Mapped[StatDelta] = mapped_column(primary_key=True)
    opp_value: Mapped[int]
    player_value: Mapped[int]
    timestamp: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[str] = mapped_column(primary_key=True)
    match_id: Mapped[str] = mapped_column(primary_key=True)

    def __repr__(self) -> str:
        return (
            f"StatDeltaEvent(player_id={self.player_id!r}, match_id={self.match_id!r})"
        )


class MetricEvent(Base):
    __tablename__ = "metric_event"
    __table_args__ = (
        ForeignKeyConstraint(
            ["match_id", "player_id"],
            ["match_detail.match_id", "match_detail.player_id"],
        ),
    )

    cs: Mapped[int]
    jungleCs: Mapped[int]
    level: Mapped[int]
    pid: Mapped[int]
    position: Mapped[Position] = composite(
        mapped_column("position_x", nullable=True),
        mapped_column("position_y", nullable=True),
    )
    timestamp: Mapped[int] = mapped_column(primary_key=True)
    total_damage_done_to_champions: Mapped[int]
    total_damage_taken: Mapped[int]
    total_gold: Mapped[int]
    xp: Mapped[int]
    player_id: Mapped[str] = mapped_column(primary_key=True)
    match_id: Mapped[str] = mapped_column(primary_key=True)


class MatchDetail(Base):
    __tablename__ = "match_detail"

    assists: Mapped[int]
    augments: Mapped[list[int]]
    carry_percentage: Mapped[float]
    champion_id: Mapped[int]
    cs: Mapped[int]
    damage: Mapped[int]
    damage_taken: Mapped[int]
    deaths: Mapped[int]
    gold: Mapped[int]
    items: Mapped[list[int]]
    jungle_cs: Mapped[int]
    keystone: Mapped[int]
    kills: Mapped[int]
    level: Mapped[int]
    player_id: Mapped[str] = mapped_column(
        ForeignKey("player.player_id"), primary_key=True
    )
    match_id: Mapped[str] = mapped_column(
        ForeignKey("match.match_id"), primary_key=True
    )
    role: Mapped[int]
    role_bound_item: Mapped[int]
    sub_style: Mapped[int]
    team_id: Mapped[TeamId]
    wards_placed: Mapped[int]
    maximum_kill_streak: Mapped[int]
    primary_style: Mapped[int]
    ps_hard_carry: Mapped[int]
    ps_team_play: Mapped[int]
    role_quest_completion: Mapped[int]
    runes: Mapped[list[int]]
    vision_score: Mapped[int]
    win: Mapped[bool]
    damage_share: Mapped[float]
    final_lvl_diff: Mapped[int]
    gold_share: Mapped[float]
    kill_participation: Mapped[float]
    skill_path: Mapped[list[int]]
    stat_shards: Mapped[list[int]]
    summoner_spells: Mapped[list[int]]
    timeline_events: Mapped[List[TimelineEvent]] = relationship(default_factory=list)
    stat_delta_events: Mapped[List[StatDeltaEvent]] = relationship(default_factory=list)
    metric_events: Mapped[List[MetricEvent]] = relationship(default_factory=list)

    def __repr__(self) -> str:
        return f"MatchDetail(player_id={self.player_id!r}, match_id={self.match_id!r})"


class Team(Base):
    __tablename__ = "team"

    team_id: Mapped[TeamId] = mapped_column(primary_key=True)
    match_id: Mapped[str] = mapped_column(
        ForeignKey("match.match_id"),
        primary_key=True,
    )
    bans: Mapped[list[int]]
    baron_kills: Mapped[int]
    dragon_kills: Mapped[int]
    gold: Mapped[int]
    inhibitor_kills: Mapped[int]
    rift_herald_kills: Mapped[int]
    tower_kills: Mapped[int]
    kills: Mapped[int]
    # TODO: backwards compatible w/ Patch 15 is other data, i.e.
    # Attakhan kills.


class Match(Base):
    __tablename__ = "match"

    match_creation_time: Mapped[int]
    match_duration_seconds: Mapped[int]
    match_id: Mapped[str] = mapped_column(primary_key=True)
    # 1:m relationships, see: https://docs.sqlalchemy.org/en/21/orm/basic_relationships.html#one-to-many
    # possible forward ref, python 3.14+
    queue_type: Mapped[QueueType]
    region_id: Mapped[Region]
    version: Mapped[GameVersion]
    team_ids: Mapped[List[Team]] = relationship()
    player_ids: Mapped[List[MatchDetail]] = relationship()

    def __repr__(self) -> str:
        return f"Match(match_id={self.match_id!r})"
