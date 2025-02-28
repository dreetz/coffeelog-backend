import datetime
from typing import Annotated
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Session, select
from sqlalchemy import func

import models
from database import get_session, create_db_and_tables

SessionDep = Annotated[Session, Depends(get_session)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)


@app.post("/coffee/")
def create_coffee(coffee: models.CoffeeBase, session: SessionDep) -> models.Coffee:
    db_coffee = models.Coffee.model_validate(coffee)
    session.add(db_coffee)
    session.commit()
    session.refresh(db_coffee)
    return db_coffee


@app.get("/coffee/")
def read_coffees(
    session: SessionDep, offset: int = 0, limit: Annotated[int, Query(le=100)] = 100
) -> list[models.Coffee]:
    coffee = session.exec(select(models.Coffee).offset(offset).limit(limit)).all()
    return coffee


@app.get("/coffee/latest")
def read_latest_coffee_id(session: SessionDep):
    coffee = session.exec(
        select(models.Coffee).order_by(models.Coffee.id.desc())
    ).first()
    if not coffee:
        raise HTTPException(status_code=404, detail="No coffee in database.")
    return coffee


@app.get("/coffee/{coffee_id}")
def read_coffee(coffee_id: int, session: SessionDep) -> models.Coffee:
    coffee = session.get(models.Coffee, coffee_id)
    if not coffee:
        raise HTTPException(status_code=404, detail="Coffee not found.")
    return coffee


@app.patch("/coffee/{coffee_id}")
def update_coffee(coffee_id: int, coffee: models.CoffeeUpdate, session: SessionDep):
    coffee_db = session.get(models.Coffee, coffee_id)
    if not coffee_db:
        raise HTTPException(status_code=404, detail="Coffee not found.")
    coffee_data = coffee.model_dump(exclude_unset=True)
    coffee_db.sqlmodel_update(coffee_data)
    session.add(coffee_db)
    session.commit()
    session.refresh(coffee_db)
    return coffee_db


@app.delete("/coffee/{coffee_id}")
def delete_coffee(coffee_id: int, session: SessionDep):
    coffee = session.get(models.Coffee, coffee_id)
    if not coffee:
        raise HTTPException(status_code=404, detail="Coffee not found.")
    session.delete(coffee)
    session.commit()
    return {"ok": True}


@app.post("/cups/")
def create_cup(cup: models.CupBase, session: SessionDep) -> models.Cup:
    db_cup = models.Cup.model_validate(cup)
    session.add(db_cup)
    session.commit()
    session.refresh(db_cup)
    return db_cup


@app.get("/cups/")
def read_cups(
    session: SessionDep, offset: int = 0, limit: Annotated[int, Query(le=100)] = 100
) -> list[models.Cup]:
    cups = session.exec(select(models.Cup).offset(offset).limit(limit)).all()
    return cups


@app.get("/cups/{cup_id}")
def read_cup(cup_id: int, session: SessionDep) -> models.Cup:
    cup = session.get(models.Cup, cup_id)
    if not cup:
        raise HTTPException(status_code=404, detail="Cup not found.")
    return cup


@app.patch("/cups/{cup_id}")
def update_cup(cup_id: int, cup: models.CupUpdate, session: SessionDep):
    cup_db = session.get(models.Cup, cup_id)
    if not cup_db:
        raise HTTPException(status_code=404, detail="Cup not found.")
    cup_data = cup.model_dump(exclude_unset=True)
    cup_db.sqlmodel_update(cup_data)
    session.add(cup_db)
    session.commit()
    session.refresh(cup_db)
    return cup_db


@app.delete("/cups/{cup_id}")
def delete_cup(cup_id: int, session: SessionDep):
    cup = session.get(models.Cup, cup_id)
    if not cup:
        raise HTTPException(status_code=404, detail="Cup not found.")
    session.delete(cup)
    session.commit()
    return {"ok": True}


@app.post("/actions/drink")
def perform_drink(user: models.User, session: SessionDep):
    """Shortcut function to add new entry in cups with given username."""

    # Load latest coffee id
    db_coffee: models.Coffee = session.exec(
        select(models.Coffee).order_by(models.Coffee.id.desc())
    ).first()

    if not db_coffee:
        raise HTTPException(status_code=404, detail="No coffee in database.")

    # Create cup object and add it to database
    cup = models.CupBase(
        username=user.username,
        coffee_id=db_coffee.id,
        date_time=datetime.datetime.now(),
    )
    db_cup = models.Cup.model_validate(cup)
    session.add(db_cup)
    session.commit()
    session.refresh(db_cup)
    return db_cup


@app.get("/actions/count")
def get_coffee_count(session: SessionDep):
    db_cups = session.exec(select(func.count(models.Cup.id))).one()
    return db_cups


@app.get("/actions/count/{username}")
def get_coffee_count_by_username(username: str, session: SessionDep):
    db_cups = session.exec(
        select(func.count(models.Cup.id)).where(models.Cup.username == username)
    ).one()
    return db_cups
