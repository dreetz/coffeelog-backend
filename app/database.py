from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.config import settings

from sqlalchemy.pool import NullPool

url = f"postgresql://{settings.DB_USER}:{settings.DB_KEY}@{settings.DB_URL}/{settings.DB_SCHEMA}"
con = create_engine(url, client_encoding="utf8", poolclass=NullPool)

connect_args = {}
engine = create_engine(url, connect_args=connect_args)


def get_session():
    with Session(engine) as session:
        yield session
