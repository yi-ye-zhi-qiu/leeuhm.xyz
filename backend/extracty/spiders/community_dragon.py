# This pulls down the latest site assets to use
# for champion images, skill icons, etc.
# https://github.com/CommunityDragon/Docs/blob/master/assets.md
#
# Assets are stored in Cloudflare R2 at
# `{asset_type}/{id}.{ext}`, with the ids we store in Postgres, e.g.
# `item/3158.png` for `MatchDetail.items`.
#
# File names don't contain our ids
# (e.g. `034_steel_shield.project_jade.png`), CommunityDragon's JSON data files
# map ids to files instead, e.g. `v1/items.json`.
#
# | R2 key                       | Postgres                                      |
# | ---------------------------- | --------------------------------------------- |
# | profile-icon/{id}.jpg        | Player.icon_id                                |
# | champion/{id}.png            | MatchDetail.champion_id, Team.bans            |
# | champion-ability/{id}/{n}.png| MatchDetail.skill_path, 1-4 (q-r), 0 passive  |
# | item/{id}.png                | MatchDetail.items, role_bound_item            |
# | rune/{id}.png                | MatchDetail.runes, keystone, stat_shards      |
# | rune-style/{id}.png          | MatchDetail.primary_style, sub_style          |
# | summoner-spell/{id}.png      | MatchDetail.summoner_spells                   |
# | rank-mini/{tier}.svg         | Player.tier                                   |
# | rank-emblem/{tier}.png       | Player.tier                                   |
# | role/{role}.png              | MatchDetail.role                              |
# | monster/{monster}.png        | TimelineEvent.monster_subtype or monster_type |

from pathlib import PurePosixPath

from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider
from extracty.items import AssetItem
from schemas import Tier


def asset(keys: str | list[str], url: str) -> AssetItem:
    """An asset of `keys`, with the source's file extension, e.g. `item/3158` and
    `.png`. Several keys when ids share a file (e.g. Flash is summoner spells 4,
    2202 and 2203), as it's only downloaded once per crawl."""
    keys = [keys] if isinstance(keys, str) else keys
    suffix = PurePosixPath(url).suffix
    return AssetItem(keys=[f"{key}{suffix}" for key in keys], file_urls=[url])


class CommunityDragonSpider(Spider):
    name = "community-dragon-spider"
    _version = "latest"
    domain = f"https://raw.communitydragon.org/{_version}/"
    public = f"{domain}/plugins/rcp-be-lol-game-data/global/default"
    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {"extracty.middlewares.Impersonate": 200},
        "DEFAULT_REQUEST_HEADERS": {"Accept": "*/*"},
        "CONCURRENT_REQUESTS": 32,
        "ITEM_PIPELINES": {"extracty.pipelines.AssetFilesPipeline": 1},
    }

    async def start(self):
        for k, v in {
            f"{self.public}/v1/items.json": self.parse_items,
            f"{self.public}/v1/perks.json": self.parse_perks,
            f"{self.public}/v1/perkstyles.json": self.parse_perk_styles,
            f"{self.public}/v1/profile-icons.json": self.parse_profile_icons,
            f"{self.public}/v1/summoner-spells.json": self.parse_summoner_spells,
            f"{self.public}/v1/champion-summary.json": self.parse_champion_summary,
        }.items():
            yield JsonRequest(k, callback=v)
        for tier in [
            "challenger",
            "grandmaster",
            "master",
            "diamond",
            "emerald",
            "platinum",
            "gold",
            "silver",
            "bronze",
            "iron",
            "unranked",
        ]:
            yield asset(
                f"rank-mini/{tier}",
                f"{self.public}/plugins/rcp-fe-lol-static-assets/global/default/images/ranked-mini-crests/{tier}.svg",
            )
            yield asset(
                f"rank-emblem/{tier}",
                f"{self.public}/plugins/rcp-fe-lol-shared-components/global/default/images/{tier}.png",
            )
        for role, position in {
            1: "jungle",
            2: "support",
            3: "bottom",
            4: "top",
            5: "middle",
        }.items():
            yield asset(
                f"role/{role}",
                f"{self.public}/plugins/rcp-fe-lol-clash/global/defautls/assets/image/positions/icon-position-{position}.png",
            )
        for monster, path in {
            "air_dragon": "sru_dragon_air/hud/dragon_air_square.png",
            "chemtech_dragon": "sru_dragon_chemtech/hud/icons2d/dragon_square_chemtech.png",
            "earth_dragon": "sru_dragon_earth/hud/dragon_square_earth.png",
            "fire_dragon": "sru_dragon_fire/hud/dragon_square_fire.png",
            "hextech_dragon": "sru_dragon_hextech/hud/icons2d/dragon_square_hextech.png",
            "water_dragon": "sru_dragon_water/hud/dragon_square_water.png",
            "elder_dragon": "sru_dragon_elder/hud/dragon_square_elder.png",
            "baron_nashor": "sru_baron/hud/baron_square.png",
            "horde": "sru_horde/hud/sru_voidgrub_square.png",
        }.items():
            yield asset(
                f"monster/{monster}", f"{self.public}/game/assets/characters/{path}"
            )

    def parse_champion_summary(self, response: Response):
        for champion in response.json():
            # Game mode variants, e.g. 60001 is `Jade_Annie`, aren't in ranked
            if champion["id"] >= 10_000:
                continue
            # -1 is "no champion", e.g. no ban
            yield asset(
                f"champion/{champion['id']}",
                game_data_url(champion["squarePortraitPath"]),
            )
            if champion["id"] != -1:
                yield JsonRequest(
                    f"{self.public}/v1/champions/{champion['id']}.json",
                    callback=self.parse_champion,
                )

    def parse_champion(self, response: Response):
        champion = response.json()
        yield asset(
            f"champion-ability/{champion['id']}/0",
            game_data_url(champion["passive"]["abilityIconPath"]),
        )
        for spell in champion["spells"]:
            skill_translation_tbl = {"q": 1, "w": 2, "e": 3, "r": 4}
            yield asset(
                f"champion-ability/{champion['id']}/{skill_translation_tbl[spell['spellKey']]}",
                game_data_url(spell["abilityIconPath"]),
            )

    def parse_items(self, response: Response):
        yield from self.parse_icons(response.json(), "item")

    def parse_perks(self, response: Response):
        yield from self.parse_icons(response.json(), "rune")

    def parse_perk_styles(self, response: Response):
        yield from self.parse_icons(response.json()["styles"], "rune-style")

    def parse_summoner_spells(self, response: Response):
        yield from self.parse_icons(response.json(), "summoner-spell")

    def parse_profile_icons(self, response: Response):
        yield from self.parse_icons(response.json(), "profile-icon")

    def parse_icons(self, entries: list[dict], asset_type: str):
        """`{asset_type}/{id}` from `id` and `iconPath`, which some lack."""
        keys_by_url: dict[str, list[str]] = {}
        # AI: give examples here please
        for entry in entries:
            if not entry.get("iconPath"):
                self.crawler.stats.inc_value(f"assets/missing_icon/{asset_type}")
                continue
            p = entry["iconPath"]
            p = p.removeprefix("/lol-game-data/assets/")
            p = p.lower()
            url = f"{self.public}/{p}"
            keys_by_url.setdefault(url, []).append(f"{asset_type}/{entry['id']}")
        for url, keys in keys_by_url.items():
            yield asset(keys, url)
