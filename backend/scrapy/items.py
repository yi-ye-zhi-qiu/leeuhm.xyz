from dataclasses import dataclass
from typing import Optional


@dataclass
class LeaderboardItem:
    iconId: int
    losses: int
    lp: int
    rank: int
    riotTagLine: str
    riotUserName: str
    summonerLevel: int
    tier: str
    wins: int


@dataclass
class TimelineEvent:
    eventType: str  # TODO: restrict to `ward_placed`, `champion_killed`, etc.
    assistId: Optional[str]
    assistRiotIds: Optional[list[str]]
    buildingType: Optional[str]
    killerId: Optional[str]
    killerIds: Optional[list[str]]
    laneType: str  # TODO: notate exact lanes
    monsterSubtype: Optional[str]
    monsterType: Optional[str]
    pid: int
    position: Optional[str]
    riotTagLine: str
    riotUserName: str
    teamId: Optional[str]
    timestamp: int
    towerType: Optional[str]  # TODO: notate with tower types
    victimId: Optional[str]
    victimRiotTagLine: Optional[str]
    victimRiotUserName: Optional[str]
    wardType: Optional[str]


@dataclass
class StatDelta:
    statType: str  # TODO: annotate with `csDifference`, `kaDifference`, `xpDifference`, `goldDifference`
    oppValue: int
    playerValue: int
    timestamp: int


@dataclass
class PlayerData:
    assists: int
    augments: list[int]
    carryPercentage: float
    championId: int
    cs: int
    damage: int
    damageTaken: int
    deaths: int
    gold: int
    items: list[int]
    jungleCs: int
    keystone: int
    kills: int
    level: int
    riotTagLine: str
    riotUserName: str
    role: int
    roleBoundItem: int
    subStyle: int
    summonerSpells: list[int]
    teamId: int
    wardsPlaced: int
    maximumKillStreak: int
    primaryStyle: int
    psHardCarry: int
    psTeamPlay: int
    riotTagLine: str
    riotUserName: str
    roleBoundItem: int
    roleQuestCompletion: int
    runes: list[int]
    summonerSpells: list[int]
    visionScore: int
    win: bool
    damageShare: float
    finalLvlDiff: float
    goldShare: float
    killParticipation: float
    skillPath: list[int]
    statShards: list[int]
    timelineEvents: list[TimelineEvent]
    statDeltas: list[StatDelta]


@dataclass
class TeamData:
    bans: list[int]
    baronKills: int
    dragonKills: int
    gold: int
    inhibitorKills: int
    kills: int
    riftHeraldKills: int
    towerKills: int


@dataclass
class MatchData:
    matchCreationTime: int
    matchDurationSeconds: int
    matchId: int
    queueType: str
    regionId: str
    version: str
    winningTeam: int


@dataclass
class MatchDetailItem:
    playerData: list[PlayerData]
    matchData: MatchData
    teamData: TeamData
