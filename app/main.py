import datetime
import json
from typing import Annotated, Optional
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models, schemas
from app.config import settings
from app.database import engine

from redis.asyncio import Redis

redis_client: Optional[Redis] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client
    redis_client = Redis.from_url(
        f"redis://{settings.REDIS_URL}:{settings.REDIS_PORT}/0"
    )
    try:
        await redis_client.ping()
        yield
    finally:
        if redis_client:
            await redis_client.aclose()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


async def get_redis() -> Redis:
    assert redis_client is not None
    return redis_client


async def cache_get_json(r: Redis, key: str):
    data = await r.get(key)
    if data is None:
        return None
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return None


async def cache_set_json(r: Redis, key: str, value, ttl: int):
    await r.set(key, json.dumps(value, default=str), ex=ttl)


async def cache_del_json(r: Redis, key: str):
    await r.delete(key)


def key_coffee() -> str:
    return f"cache:coffee:all"


def key_latest() -> str:
    return "cache:meta:coffee:latest"


def key_total() -> str:
    return "cache:meta:total"


def key_total_user(user: str) -> str:
    return f"cache:meta:total:{user}"


def key_today() -> str:
    return f"cache:meta:today"


def key_today_user(user: str) -> str:
    return f"cache:meta:today:{user}"


@app.post("/coffee/")
async def create_coffee(
    coffee: schemas.CoffeeBase, r: Redis = Depends(get_redis)
) -> schemas.Coffee:
    with Session(engine) as session:
        db_coffee = models.Coffee(**coffee.model_dump())
        session.add(db_coffee)
        session.commit()
        session.refresh(db_coffee)

        k = key_latest()
        await cache_del_json(r, k)

        return db_coffee


@app.get("/coffee/")
def read_coffees(
    offset: int | None = None, limit: int | None = None
) -> list[schemas.Coffee]:
    with Session(engine) as session:
        coffee = session.scalars(select(models.Coffee).offset(offset).limit(limit)).all()
        return list(coffee)


@app.get("/coffee/latest", response_model=schemas.Coffee)
async def read_latest_coffee_id(
    response: Response, r: Redis = Depends(get_redis)
):
    k = key_latest()
    cached = await cache_get_json(r, k)

    if cached:
        response.headers["x-cache"] = "hit"
        return cached

    with Session(engine) as session:
        db_coffee = session.scalars(
            select(models.Coffee).order_by(models.Coffee.id.desc())
        ).first()
        if not db_coffee:
            raise HTTPException(status_code=404, detail="No coffee in database.")

        coffee = schemas.Coffee(**db_coffee.__dict__)
        response.headers["x-cache"] = "miss"

        await cache_set_json(r, k, coffee.model_dump(), ttl=300)
        return coffee


@app.get("/coffee/{coffee_id}")
def read_coffee(coffee_id: int) -> schemas.Coffee:
    with Session(engine) as session:
        coffee = session.get(models.Coffee, coffee_id)
        if not coffee:
            raise HTTPException(status_code=404, detail="Coffee not found.")
        return coffee


@app.patch("/coffee/{coffee_id}")
async def update_coffee(
    coffee_id: int,
    coffee: schemas.CoffeeUpdate,
    r: Redis = Depends(get_redis),
):
    with Session(engine) as session:
        stmt = select(models.Coffee).where(models.Coffee.id == coffee_id)
        coffee_db = session.scalars(stmt).first()

        if not coffee_db:
            raise HTTPException(status_code=404, detail="Coffee not found.")
        coffee_data = coffee.model_dump(exclude_unset=True)

        for key, value in coffee_data.items():
            coffee_db.__setattr__(key, value)

        session.commit()
        session.refresh(coffee_db)

        k = key_latest()
        await cache_del_json(r, k)

        return coffee_db


@app.delete("/coffee/{coffee_id}")
async def delete_coffee(
    coffee_id: int, r: Redis = Depends(get_redis)
):
    with Session(engine) as session:
        coffee = session.get(models.Coffee, coffee_id)
        if not coffee:
            raise HTTPException(status_code=404, detail="Coffee not found.")
        session.delete(coffee)
        session.commit()

    await cache_del_json(r, key_latest())
    await cache_del_json(r, key_today())
    await cache_del_json(r, key_total())

    return {"ok": True}


@app.post("/cups/")
async def create_cup(
    cup: schemas.CupBase, r: Redis = Depends(get_redis)
) -> schemas.Cup:
    with Session(engine) as session:
        db_cup = models.Cup(**cup.model_dump())
        session.add(db_cup)
        session.commit()
        session.refresh(db_cup)

    await cache_del_json(r, key_today())
    await cache_del_json(r, key_today_user(cup.username))
    await cache_del_json(r, key_total())
    await cache_del_json(r, key_total_user(cup.username))

    return db_cup


@app.get("/cups/")
def read_cups(
    offset: int = 0, limit: Annotated[int, Query(le=100)] = 100
) -> list[schemas.Cup]:
    with Session(engine) as session:
        cups = session.scalars(select(models.Cup).offset(offset).limit(limit)).all()
        return list(cups)


@app.get("/cups/{cup_id}")
def read_cup(cup_id: int) -> schemas.Cup:
    with Session(engine) as session:
        cup = session.get(models.Cup, cup_id)
        if not cup:
            raise HTTPException(status_code=404, detail="Cup not found.")
        return cup


@app.patch("/cups/{cup_id}")
def update_cup(cup_id: int, cup: schemas.CupUpdate):
    with Session(engine) as session:
        stmt = select(models.Cup).where(models.Cup.id == cup_id)
        cup_db = session.scalars(stmt).first()

        if not cup_db:
            raise HTTPException(status_code=404, detail="Cup not found.")
        cup_data = cup.model_dump(exclude_unset=True)

        for key, value in cup_data.items():
            cup_db.__setattr__(key, value)

        session.commit()
        session.refresh(cup_db)
        return cup_db


@app.delete("/cups/{cup_id}")
async def delete_cup(cup_id: int, r: Redis = Depends(get_redis)):
    with Session(engine) as session:
        db_cup = session.get(models.Cup, cup_id)
        if not db_cup:
            raise HTTPException(status_code=404, detail="Cup not found.")
        cup = schemas.Cup(**db_cup.__dict__)
        session.delete(db_cup)
        session.commit()

    await cache_del_json(r, key_today())
    await cache_del_json(r, key_today_user(cup.username))
    await cache_del_json(r, key_total())
    await cache_del_json(r, key_total_user(cup.username))

    return {"ok": True}


@app.post("/actions/drink")
async def perform_drink(
    user: schemas.User, r: Redis = Depends(get_redis)
):
    """Shortcut function to add new entry in cups with given username."""
    with Session(engine) as session:
        # Load latest coffee id
        db_coffee: models.Coffee = session.scalars(
            select(models.Coffee).order_by(models.Coffee.id.desc())
        ).first()

        if not db_coffee:
            raise HTTPException(status_code=404, detail="No coffee in database.")

        # Create cup object and add it to database
        db_cup = models.Cup(
            username=user.username,
            coffee_id=db_coffee.id,
            date_time=datetime.datetime.now(),
        )
        session.add(db_cup)
        session.commit()
        session.refresh(db_cup)

    await cache_del_json(r, key_today())
    await cache_del_json(r, key_today_user(user.username))
    await cache_del_json(r, key_total())
    await cache_del_json(r, key_total_user(user.username))

    return db_cup


@app.get("/actions/count/total", response_model=int)
async def get_coffee_count_total(
   response: Response, r: Redis = Depends(get_redis)
):
    k = key_total()
    cached = await cache_get_json(r, k)

    if cached:
        response.headers["x-cache"] = " hit"
        return cached

    with Session(engine) as session:
        db_cups: int = session.scalars(select(func.count(models.Cup.id))).one()
        response.headers["x-cache"] = " miss"

        await cache_set_json(r, k, db_cups, ttl=30)
        return db_cups


@app.get("/actions/count/total/{username}", response_model=int)
async def get_coffee_count_total_username(
    username: str,
    response: Response,
    r: Redis = Depends(get_redis),
):
    k = key_total_user(username)
    cached = await cache_get_json(r, k)

    if cached:
        response.headers["x-cached"] = "hit"
        return cached

    with Session(engine) as session:
        db_cups: int = session.scalars(
            select(func.count(models.Cup.id)).where(models.Cup.username == username)
        ).one()
        response.headers["x-cached"] = "miss"

        await cache_set_json(r, k, db_cups, ttl=30)
        return db_cups


@app.get("/actions/count/today", response_model=int)
async def get_coffee_count_today(
    response: Response, r: Redis = Depends(get_redis)
):
    k = key_today()
    cached = await cache_get_json(r, k)

    if cached:
        response.headers["x-cache"] = "hit"
        return cached

    with Session(engine) as session:
        db_cups: int = session.scalars(
            select(func.count(models.Cup.id)).where(
                models.Cup.date_time >= datetime.date.today()
            )
        ).one()
        response.headers["x-cache"] = "miss"

        await cache_set_json(r, k, db_cups, ttl=10)
        return db_cups


@app.get("/actions/count/today/{username}", response_model=int)
async def get_coffee_count_today_username(
    username: str,
    response: Response,
    r: Redis = Depends(get_redis),
):
    k = key_today_user(username)
    cached = await cache_get_json(r, k)

    if cached:
        response.headers["x-cache"] = "hit"
        return cached

    with Session(engine) as session:
        db_cups: int = session.scalars(
            select(func.count(models.Cup.id)).where(
                models.Cup.username == username,
                models.Cup.date_time >= datetime.date.today(),
            )
        ).one()
        response.headers["x-cache"] = "miss"

        await cache_set_json(r, k, db_cups, ttl=30)
        return db_cups
