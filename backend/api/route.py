import os
import requests
import psycopg2
from crawl.endpoints import UGGMatchDetail, UGGMatchSummary
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

@app.get("/refresh/[id]")
async def refresh():
    """NOTE: this may fail, given it's an API request."""
    matches = requests.get(
        url=UGGMatchSummary.url(),
        data=UGGMatchSummary.payload(region="na1", ...)
    )
    new = check_if_match_summary_already_crawled()
    # Already up-to-date
    if not new:
        return {}
    for match in matches:
        requests.get(
            url=UGGMatchDetail.url(),
            data=UGGMatchDetail.payload(region="", ...),
        )

@app.get("/matches/[riotUserName]")
async def matches(riotUserName):
    connection = psycopg2.connect(os.environ["DATABASE_URL"])
    connection.autocommit = True
    cursor = connection.cursor()
    return cursor.execute(
        """
        SELECT *
        FROM MatchData
        WHERE %(riotUserName) in riotUserNames 
        """
    )

@app.get("/matchdetails/[matchId]")
async def matchDetails(matchId, riotUserName):
    connection = psycopg2.connect(os.environ["DATABASE_URL"])
    connection.autocommit = True
    cursor = connection.cursor()
    return cursor.execute(
        """
        SELECT *
        FROM PlayerData
        WHERE matchId = %(matchId)s AND riotUserName = %(riotUserName)s
        """
    )
