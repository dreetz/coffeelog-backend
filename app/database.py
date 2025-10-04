from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.config import settings

url = f"postgresql://{settings.DB_USER}:{settings.DB_KEY}@{settings.DB_URL}/{settings.DB_SCHEMA}"
connect_args = {}
engine = create_engine(url, connect_args=connect_args)


# TODO Implement async queue
def get_session():
    with Session(engine) as session:
        try:
            yield session
        except Exception as err:
            session.rollback()
            print(err)
        finally:
            session.close()
