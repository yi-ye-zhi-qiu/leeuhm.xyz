from _typeshed import AnnotationForm
from typing import Annotated

import requests
from sqlalchemy import Sequence, select
from sqlalchemy.orm import Session
from db import db, execute_statement
from fastapi import FastAPI, status, Depends, HTTPException
from models import Base, Match, MatchDetail, Player, Region
from db import engine
from ..endpoints import UGGMatchDetail, UGGMatch, UGGPlayer

app = FastAPI()

Base.metadata.create_all(bind=engine)


@app.get("/refresh/{region}/{player_id}")
async def refresh(region: Region, player_id: str, page_index: int = 0, db: Annotated[Session, Depends(db)]):
    """NOTE: this may fail, given it's an API request."""
    stmt = select(Player.riot_tag_line, Player.riot_user_name).where(
        (Player.player_id == player_id)
        & (Player.region == region)
    )
    rows: Sequence[Player] = db.execute(stmt)
    riot_user_name, riot_tag_line = rows[0]
    matches = requests.get(
        url=UGGMatch().url(),
        data=UGGMatch().payload(
            region=region,
            riot_user_name=riot_user_name,
            riot_tag_line=riot_tag_line,
            page_index=page_index,
        ),
    )
    try:
        # derive latest match
        matches = response.json()["data"]["fetchPlayerMatchSummaries"]["matchSummaries"]
        latest = matches[0]["matchId"]
        # insert latest X match ids that do not already exist
        stmt: Sequence[Match] = select(Match).where(Match.match_id == latest_match_id)
        if db.execute(stmt):
            return
        for match in matches:
            match_id = match["matchId"]
            version = match["version"]
            match_detail = UGGMatchDetail(
                region=region,
                match_id=match_id,
                version=version,
                riot_user_name=riot_user_name,
                riot_tag_line=riot_tag_line
            )
            requests.get(
                url=match_detail.url(),
                data=match_detail.payload(),
            )
    except requests.HTTPError:
        raise HTTPException("refresh:%d", matches.status_code)


@app.get("/match/{player_id}", response_model=Sequence[Match])
async def match(player_id: str, db: Annotated[Session, Depends(db)]):
    return db.execute(select(Match).where(Match.player_id == player_id))


@app.get("/match_detail/{match_id}/{player_id}", response_model=Sequence[MatchDetail])
async def match_detail(
    match_id: str, player_id: str, db: Annotated[Session, Depends(db)]
):
    return db.execute(
        select(MatchDetail).where(
            (MatchDetail.player_id == player_id) & (MatchDetail.match_id == match_id)
        )
    )


@app.get("/leaderboard/{region}/{page_index}", response_model=Sequence[Player])
async def leaderboard(region: Region, page_index: int, db: Annotated[Session, Depends(db)]):
    return db.execute(select(Player).where(Player.region == region).order_by("lp").limit(page_index * 100))


@app.get("/player/{player_id}", response_model=Player)
async def player(player_id: str, db: Annotated[Session, Depends(db)]):
    return db.execute(select(Player).where(Player.player_id == player_id))
