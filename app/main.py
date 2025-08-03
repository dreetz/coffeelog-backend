import datetime
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_session

SessionDep = Annotated[Session, Depends(get_session)]


app = FastAPI()


@app.post("/coffee/")
def create_coffee(coffee: schemas.CoffeeBase, session: SessionDep) -> schemas.Coffee:
    db_coffee = models.Coffee(**coffee.model_dump())
    session.add(db_coffee)
    session.commit()
    session.refresh(db_coffee)
    return db_coffee


@app.get("/coffee/")
def read_coffees(
    session: SessionDep, offset: int = 0, limit: Annotated[int, Query(le=100)] = 100
) -> list[schemas.Coffee]:
    coffee = session.scalars(select(models.Coffee).offset(offset).limit(limit)).all()
    return list(coffee)


@app.get("/coffee/latest")
def read_latest_coffee_id(session: SessionDep):
    coffee = session.scalars(
        select(models.Coffee).order_by(models.Coffee.id.desc())
    ).first()
    if not coffee:
        raise HTTPException(status_code=404, detail="No coffee in database.")
    return coffee


@app.get("/coffee/{coffee_id}")
def read_coffee(coffee_id: int, session: SessionDep) -> schemas.Coffee:
    coffee = session.get(models.Coffee, coffee_id)
    if not coffee:
        raise HTTPException(status_code=404, detail="Coffee not found.")
    return coffee


@app.patch("/coffee/{coffee_id}")
def update_coffee(coffee_id: int, coffee: schemas.CoffeeUpdate, session: SessionDep):
    stmt = select(models.Coffee).where(models.Coffee.id == coffee_id)
    coffee_db = session.scalars(stmt).first()

    if not coffee_db:
        raise HTTPException(status_code=404, detail="Coffee not found.")
    coffee_data = coffee.model_dump(exclude_unset=True)

    for key, value in coffee_data.items():
        coffee_db.__setattr__(key, value)

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
def create_cup(cup: schemas.CupBase, session: SessionDep) -> schemas.Cup:
    db_cup = models.Cup(**cup.model_dump())
    session.add(db_cup)
    session.commit()
    session.refresh(db_cup)
    return db_cup


@app.get("/cups/")
def read_cups(
    session: SessionDep, offset: int = 0, limit: Annotated[int, Query(le=100)] = 100
) -> list[schemas.Cup]:
    cups = session.scalars(select(models.Cup).offset(offset).limit(limit)).all()
    return list(cups)


@app.get("/cups/{cup_id}")
def read_cup(cup_id: int, session: SessionDep) -> schemas.Cup:
    cup = session.get(models.Cup, cup_id)
    if not cup:
        raise HTTPException(status_code=404, detail="Cup not found.")
    return cup


@app.patch("/cups/{cup_id}")
def update_cup(cup_id: int, cup: schemas.CupUpdate, session: SessionDep):
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
def delete_cup(cup_id: int, session: SessionDep):
    cup = session.get(models.Cup, cup_id)
    if not cup:
        raise HTTPException(status_code=404, detail="Cup not found.")
    session.delete(cup)
    session.commit()
    return {"ok": True}


@app.post("/actions/drink")
def perform_drink(user: schemas.User, session: SessionDep):
    """Shortcut function to add new entry in cups with given username."""

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
    return db_cup


@app.get("/actions/count/total")
def get_coffee_count_total(session: SessionDep):
    db_cups = session.scalars(select(func.count(models.Cup.id))).one()
    return db_cups


@app.get("/actions/count/total/{username}")
def get_coffee_count_total_username(username: str, session: SessionDep):
    db_cups = session.scalars(
        select(func.count(models.Cup.id)).where(models.Cup.username == username)
    ).one()
    return db_cups


@app.get("/actions/count/today")
def get_coffee_count_today(session: SessionDep):
    db_cups = session.scalars(
        select(func.count(models.Cup.id)).where(
            models.Cup.date_time >= datetime.date.today()
        )
    ).one()
    return db_cups


@app.get("/actions/count/today/{username}")
def get_coffee_count_today_username(username: str, session: SessionDep):
    db_cups = session.scalars(
        select(func.count(models.Cup.id)).where(
            models.Cup.username == username,
            models.Cup.date_time >= datetime.date.today(),
        )
    ).one()
    return db_cups
