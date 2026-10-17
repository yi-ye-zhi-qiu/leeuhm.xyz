"""Annontated declarative table configuration of leeuhm.xyz, see `schemas` for
value types (enums, `Position`) and Pydantic schemas."""

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

from schemas import (
    GameVersion,
    Position,
    QueueType,
    Rank,
    Region,
    StatDelta,
    TeamId,
    Tier,
)

metadata_obj = MetaData(
    # PostgreSQL has a limit of 63 characters
    naming_convention={"uq": "uq_%(table_name)s_%(column_0_N_name)s"}
)


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
    # Index of the event in the match timeline; `timestamp` isn't unique, e.g.
    # a double kill is 2 `champion_kill` events at the same timestamp.
    event_index: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[Optional[TeamId]] = mapped_column(nullable=True)
    event_type: Mapped[str]  # TODO: restrict to `ward_placed`, `champion_killed`, etc.
    assist_ids: Mapped[Optional[list[int]]]
    assist_riot_ids: Mapped[Optional[list[str]]]
    building_type: Mapped[Optional[str]]
    killer_id: Mapped[Optional[int]]
    killer_ids: Mapped[Optional[list[int]]]
    lane_type: Mapped[Optional[str]]  # TODO: notate exact lanes
    monster_subtype: Mapped[Optional[str]]
    monster_type: Mapped[Optional[str]]
    pid: Mapped[Optional[int]]  # null for `building_kill`
    position: Mapped[Position] = composite(
        mapped_column("position_x", nullable=True),
        mapped_column("position_y", nullable=True),
    )
    timestamp: Mapped[int]
    tower_type: Mapped[Optional[str]]  # TODO: notate with tower types
    victim_id: Mapped[Optional[int]]
    victim_player_id: Mapped[Optional[str]]
    ward_type: Mapped[Optional[str]]

    def __repr__(self) -> str:
        return (
            f"TimelineEvent(player_id={self.player_id!r}, match_id={self.match_id!r})"
        )


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
    jungle_cs: Mapped[int]
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
    role_quest_completion: Mapped[Optional[int]]
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
    # Participants (10 for 5v5), see `make_player_id`. Not a foreign key, as
    # participants aren't necessarily in `player` if we haven't crawled their
    # page from a leaderboard.
    player_ids: Mapped[list[str]]
    team_ids: Mapped[List[Team]] = relationship()
    match_details: Mapped[List[MatchDetail]] = relationship()

    def __repr__(self) -> str:
        return f"Match(match_id={self.match_id!r})"
