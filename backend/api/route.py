import asyncio
from contextlib import asynccontextmanager
from typing import Annotated

import requests
from fastapi import Depends, FastAPI, HTTPException, Path
from sqlalchemy import any_, select, func, cast, Float, Numeric
from sqlalchemy.ext.asyncio import AsyncSession

from db import db, engine
from endpoints import UGGMatch, UGGMatchDetail
from models import Match, MatchDetail, Player
from schemas import (
    LeaderboardPage,
    LeaderboardPlayerSchema,
    MatchDetailSchema,
    MatchSchema,
    PlayerSchema,
    Region,
)

LEADERBOARD_PAGE_SIZE = 100


# see: https://fastapi.tiangolo.com/advanced/events/
@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Schema is managed by migrations (Alembic) not by app startup
    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)


async def post_graphql(url: str, payload: dict) -> requests.Response:
    """POST a u.gg GraphQL query, in a thread as `requests` is blocking."""
    response = await asyncio.to_thread(requests.post, url, json=payload, timeout=30)
    response.raise_for_status()
    return response


@app.get("/search/{region}/{player_name}")
async def search(
    region: Region,
    player_name: str,
):
    # TODO: Implement elastisearch to provide searchable user names
    pass


@app.get("/refresh/{region}/{player_id}")
async def refresh(
    region: Region,
    player_id: str,
    session: Annotated[AsyncSession, Depends(db)],
    page_index: int = 1,
) -> dict[str, int]:
    """Crawl a player's latest matches (and their details) if there are new ones.

    Returns the number of rows written per table.
    """
    # TODO: replace with Riot API
    player = (
        await session.execute(
            select(Player.riot_user_name, Player.riot_tag_line).where(
                (Player.player_id == player_id) & (Player.region == region)
            )
        )
    ).one_or_none()
    if player is None:
        raise HTTPException(status_code=404, detail=f"unknown_player:{player_id}")
    riot_user_name, riot_tag_line = player
    try:
        response = await post_graphql(
            UGGMatch().url(),
            UGGMatch().payload(
                region=region,
                riot_user_name=riot_user_name,
                riot_tag_line=riot_tag_line,
                page_index=page_index,
            ),
        )
        matches = response.json()["data"]["fetchPlayerMatchSummaries"]["matchSummaries"]
        if not matches:
            return {}
        latest_match_id = str(matches[0]["matchId"])
        if await session.get(Match, latest_match_id) is not None:
            return {}
        n_written = {"match": await UGGMatch().insert(response)}
        for match in matches:
            match_detail = UGGMatchDetail(
                region=region,
                match_id=match["matchId"],
                version=match["version"],
                riot_user_name=riot_user_name,
                riot_tag_line=riot_tag_line,
            )
            response = await post_graphql(match_detail.url(), match_detail.payload())
            for table, n_rows in (await match_detail.insert(response)).items():
                n_written[table] = n_written.get(table, 0) + n_rows
        return n_written
    except requests.HTTPError as error:
        raise HTTPException(
            status_code=502,
            detail=f"unsuccessful_refresh:{error.response.status_code}",
        )


@app.get("/match/{player_id}", response_model=list[MatchSchema])
async def match(player_id: str, session: Annotated[AsyncSession, Depends(db)]):
    # Matches the player participated in, latest first
    return (
        await session.scalars(
            select(Match)
            .where(player_id == any_(Match.player_ids))
            .order_by(Match.match_creation_time.desc())
        )
    ).all()


@app.get("/match_detail/{match_id}/{player_id}", response_model=list[MatchDetailSchema])
async def match_detail(
    match_id: str, player_id: str, session: Annotated[AsyncSession, Depends(db)]
):
    return (
        await session.scalars(
            select(MatchDetail).where(
                (MatchDetail.player_id == player_id)
                & (MatchDetail.match_id == match_id)
            )
        )
    ).all()


@app.get(
    "/leaderboard/{region}/{page_index}",
    response_model=LeaderboardPage[LeaderboardPlayerSchema],
)
async def leaderboard(
    region: Region,
    session: Annotated[AsyncSession, Depends(db)],
    page_index: Annotated[int, Path(ge=1)],
):

    where = Player.region == region
    total = await session.scalar(select(func.count()).select_from(Player).where(where))
    rows = (
        await session.execute(
            select(
                *Player.__table__.columns,
                (
                    func.round(
                        cast(Player.wins, Numeric)
                        / (Player.wins + Player.losses)
                        * 100,
                        2,
                    )
                ).label("win_rate"),
            )
            .where(where)
            .order_by(Player.lp.desc().nulls_last())
            .offset((page_index - 1) * LEADERBOARD_PAGE_SIZE)
            .limit(LEADERBOARD_PAGE_SIZE)
        )
    ).all()
    return LeaderboardPage(
        items=rows, total=total, page_index=page_index, page_size=LEADERBOARD_PAGE_SIZE
    )


@app.get("/player/{player_id}", response_model=PlayerSchema)
async def player(player_id: str, session: Annotated[AsyncSession, Depends(db)]):
    player = await session.get(Player, player_id)
    if player is None:
        raise HTTPException(status_code=404, detail=f"unknown_player:{player_id}")
    return player
