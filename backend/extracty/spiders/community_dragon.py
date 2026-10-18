# This pulls down the latest site assets to use
# for champion images, skill icons, etc.
# https://github.com/CommunityDragon/Docs/blob/master/assets.md
#
# That data is not organized, so we make it organized like this:
#
# | Asset store (Cloudflare R2)  | Postgres                                      |
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


from scrapy import Request
from pathlib import PurePosixPath
from scrapy.spiders import Spider
from scrapy.http import JsonRequest, Response

from extracty.items import AssetItem


class CommunityDragonSpider(Spider):
    name = "community-dragon-spider"
    _version = "latest"
    domain = f"https://raw.communitydragon.org/{_version}"
    public = f"{domain}/plugins/rcp-be-lol-game-data/global/default"
    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {"extracty.middlewares.Impersonate": 200},
        "DEFAULT_REQUEST_HEADERS": {"Accept": "*/*"},
        "CONCURRENT_REQUESTS": 32,
        "ITEM_PIPELINES": {"extracty.pipelines.CloudfareR2StorageConnector": 1},
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
            # e.g. .../ranked-mini-crests/challenger.svg -> rank-mini/challenger.svg,
            # only SVGs exist for every tier (there's no emerald.png)
            yield Request(
                f"{self.domain}/plugins/rcp-fe-lol-static-assets/global/default/images/ranked-mini-crests/{tier}.svg",
                callback=self.parse,
                cb_kwargs={"key": f"rank-mini/{tier}"},
            )
            # e.g. .../images/challenger.png -> rank-emblem/challenger.png
            yield Request(
                f"{self.domain}/plugins/rcp-fe-lol-shared-components/global/default/images/{tier}.png",
                callback=self.parse,
                cb_kwargs={"key": f"rank-emblem/{tier}"},
            )
        # u.gg's `MatchDetail.role`, e.g. icon-position-jungle.png -> role/1.png
        for role, position in {
            1: "jungle",
            2: "utility",  # i.e. support
            3: "bottom",
            4: "top",
            5: "middle",
        }.items():
            yield Request(
                f"{self.domain}/plugins/rcp-fe-lol-clash/global/default/assets/images/position-selector/positions/icon-position-{position}.png",
                callback=self.parse,
                cb_kwargs={"key": f"role/{role}"},
            )
        # `TimelineEvent.monster_subtype` (dragons) or `monster_type` (others),
        # e.g. dragon_square_water.png -> monster/water_dragon.png. There's no
        # pattern to these file names.
        for monster, path in {
            "air_dragon": "sru_dragon_air/hud/dragon_air_square.png",
            "chemtech_dragon": "sru_dragon_chemtech/hud/icons2d/dragon_square_chemtech.png",
            "earth_dragon": "sru_dragon_earth/hud/dragon_square_earth.png",
            "fire_dragon": "sru_dragon_fire/hud/dragon_square_fire.png",
            "hextech_dragon": "sru_dragon_hextech/hud/icons2d/dragon_square_hextech.png",
            "water_dragon": "sru_dragon_water/hud/dragon_square_water.png",
            "elder_dragon": "sru_dragon_elder/hud/dragon_square_elder.png",
            "baron_nashor": "sru_baron/hud/baron_square.png",
            "riftherald": "sru_riftherald/hud/sruriftherald_square.png",
            "horde": "sru_horde/hud/sru_voidgrub_square.png",
        }.items():
            yield Request(
                f"{self.domain}/game/assets/characters/{path}",
                callback=self.parse,
                cb_kwargs={"key": f"monster/{monster}"},
            )

    def parse_champion_summary(self, response: Response):
        # e.g. {"id": 75, "alias": "Nasus",
        #       "squarePortraitPath": "/lol-game-data/assets/v1/champion-icons/75.png"}
        #   -> champion/75.png, and v1/champions/75.json for its abilities
        for champion in response.json():
            # Game mode variants, e.g. 60001 is `Jade_Annie`, aren't in ranked
            if champion["id"] >= 10_000:
                continue
            # -1 is "no champion", e.g. no ban
            path = champion["squarePortraitPath"].removeprefix("/lol-game-data/assets/")
            yield Request(
                f"{self.public}/{path.lower()}",
                callback=self.parse,
                cb_kwargs={"key": f"champion/{champion['id']}"},
            )
            if champion["id"] != -1:
                yield JsonRequest(
                    f"{self.public}/v1/champions/{champion['id']}.json",
                    callback=self.parse_champion,
                )

    def parse_champion(self, response: Response):
        # e.g. {"id": 75,
        #       "passive": {"abilityIconPath": ".../Nasus/HUD/Icons2D/Nasus_Passive.png"},
        #       "spells": [{"spellKey": "q", "abilityIconPath": ".../Nasus_Q.png"}, ...]}
        #   -> champion-ability/75/0.png (passive), champion-ability/75/1.png (q), ...
        # matching `MatchDetail.skill_path`, e.g. [1, 2, 3, 1, ...] is q, w, e, q
        champion = response.json()
        abilities = [("0", champion["passive"])]
        skill_translation_tbl = {"q": "1", "w": "2", "e": "3", "r": "4"}
        for spell in champion["spells"]:
            abilities.append((skill_translation_tbl[spell["spellKey"]], spell))
        for slot, ability in abilities:
            path = ability["abilityIconPath"].removeprefix("/lol-game-data/assets/")
            yield Request(
                f"{self.public}/{path.lower()}",
                callback=self.parse,
                cb_kwargs={"key": f"champion-ability/{champion['id']}/{slot}"},
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
        # e.g. an `items.json` entry
        #   {"id": 1001, "name": "Boots",
        #    "iconPath": "/lol-game-data/assets/ASSETS/Items/Icons2D/1001_Class_T1_BootsofSpeed.png"}
        # is downloaded from
        #   {public}/assets/items/icons2d/1001_class_t1_bootsofspeed.png
        # and stored at `item/1001.png`
        for entry in entries:
            if not entry.get("iconPath"):
                # e.g. 86 profile icons, `{"id": 29, "iconPath": None}`
                self.crawler.stats.inc_value(f"assets/missing_icon/{asset_type}")
                continue
            path = entry["iconPath"].removeprefix("/lol-game-data/assets/")
            yield Request(
                f"{self.public}/{path.lower()}",
                callback=self.parse,
                cb_kwargs={"key": f"{asset_type}/{entry['id']}"},
                # Ids can share a file, e.g. Flash is summoner spells 4, 2202
                # and 2203, which is then downloaded for each
                dont_filter=True,
            )

    def parse(self, response: Response, key: str):
        # The file's extension, e.g. `item/1001` and `.png` is `item/1001.png`
        yield AssetItem(
            key=f"{key}{PurePosixPath(response.url).suffix}",
            url=response.url,
            body=response.body,
        )
