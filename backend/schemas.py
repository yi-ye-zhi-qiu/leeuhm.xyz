import enum
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


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


class StatDelta(enum.Enum):
    cs_difference = "cs_difference"
    ka_difference = "ka_difference"
    xp_difference = "xp_difference"
    gold_difference = "gold_difference"


def make_player_id(*args, riot_user_name: str, riot_tag_line: str):
    return f"{riot_user_name}#{riot_tag_line}"


# A dataclass (not a Pydantic model) as it's also the `composite` type of
# `TimelineEvent.position` and `MetricEvent.position`.
@dataclass
class Position:  # e.g. [{x: 603, y: 611}]
    x: Optional[int]
    y: Optional[int]


class Schema(BaseModel):
    # Allows `PlayerSchema.model_validate(player)` from a `models.Player`
    model_config = ConfigDict(from_attributes=True)


class PlayerSchema(Schema):
    player_id: str
    riot_user_name: str
    riot_tag_line: str
    region: Region
    icon_id: int
    summoner_level: int
    wins: int
    losses: int
    lp: Optional[int]
    rank: Optional[Rank]
    tier: Optional[Tier]
    updated_at: datetime


class LeaderboardPlayerSchema(PlayerSchema):
    win_rate: float


class LeaderboardPage[T](BaseModel):
    items: list[T]
    total: int
    page_index: int
    page_size: int

    @property
    def n_pages(self) -> int:
        return -(-self.total // self.page_size)


class MatchSchema(Schema):
    match_id: str
    match_creation_time: int
    match_duration_seconds: int
    queue_type: QueueType
    region_id: Region
    version: GameVersion
    player_ids: list[str]


class TeamSchema(Schema):
    match_id: str
    team_id: TeamId
    bans: list[int]
    baron_kills: int
    dragon_kills: int
    gold: int
    inhibitor_kills: int
    rift_herald_kills: int
    tower_kills: int
    kills: int


class MatchDetailSchema(Schema):
    match_id: str
    player_id: str
    team_id: TeamId
    assists: int
    augments: list[int]
    carry_percentage: float
    champion_id: int
    cs: int
    damage: int
    damage_taken: int
    deaths: int
    gold: int
    items: list[int]
    jungle_cs: int
    keystone: int
    kills: int
    level: int
    role: int
    role_bound_item: int
    sub_style: int
    wards_placed: int
    maximum_kill_streak: int
    primary_style: int
    ps_hard_carry: int
    ps_team_play: int
    role_quest_completion: Optional[int]
    runes: list[int]
    vision_score: int
    win: bool
    damage_share: float
    final_lvl_diff: int
    gold_share: float
    kill_participation: float
    skill_path: list[int]
    stat_shards: list[int]
    summoner_spells: list[int]


class TimelineEventSchema(Schema):
    match_id: str
    player_id: str
    event_index: int
    team_id: Optional[TeamId]
    event_type: str
    assist_ids: Optional[list[int]]
    assist_riot_ids: Optional[list[str]]
    building_type: Optional[str]
    killer_id: Optional[int]
    killer_ids: Optional[list[int]]
    lane_type: Optional[str]
    monster_subtype: Optional[str]
    monster_type: Optional[str]
    pid: Optional[int]
    position: Position
    timestamp: int
    tower_type: Optional[str]
    victim_id: Optional[int]
    victim_player_id: Optional[str]
    ward_type: Optional[str]


class StatDeltaEventSchema(Schema):
    match_id: str
    player_id: str
    stat_type: StatDelta
    timestamp: int
    opp_value: int
    player_value: int


class MetricEventSchema(Schema):
    match_id: str
    player_id: str
    timestamp: int
    cs: int
    jungle_cs: int
    level: int
    pid: int
    position: Position
    total_damage_done_to_champions: int
    total_damage_taken: int
    total_gold: int
    xp: int
