import os
from pydantic_settings import BaseSettings
from sqlalchemy import URL


class Settings(BaseSettings):
    db_username: str  # TODO: comes from secret manager
    db_password: str
    pg_host: str
    pg_database: str
    db_url: URL


settings = Settings(
    db_username=os.environ["DB_USERNAME"],
    db_password=os.environ["DB_PASSWORD"],
    pg_host=os.environ["PG_HOST"],
    pg_database="leeuhmxyz",
    db_url=URL.create(
        "postgresql+psycopg",
        username=os.environ["DB_USERNAME"],
        password=os.environ["DB_PASSWORD"],
        host=os.environ["PG_HOST"],
        database="leeuhmxyz",
    ),
)
