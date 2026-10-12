import os
from sqlalchemy import URL, create_engine, text
from sqlalchemy.orm import sessionmaker

# TODO: make it respect env.py
url_object = URL.create(
    "postgresql+pg8000",
    username="dbuser",
    password=os.environ["DB_PASSWORD"],
    host="pghost10",
    database="leeuhmgg",
)

engine = create_engine(url_object)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def db():
    with SessionLocal() as db:
        yield db


def execute_statement(statement: str):
    with engine.connect() as connection:
        result = connection.execute(text(statement))
        return result
