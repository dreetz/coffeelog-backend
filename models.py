from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime, date


class CoffeeBase(SQLModel):
    roasting_facility: str
    coffee_name: str
    size_g: int
    roast_date: date | None
    open_date: date | None
    price: float | None


class Coffee(CoffeeBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    cups: list["Cup"] = Relationship(back_populates="coffee")


class CoffeeUpdate(CoffeeBase):
    roasting_facility: str | None = None
    coffee_name: str | None = None
    size_g: int | None = None
    roast_date: date | None = None
    open_date: date | None = None
    price: float | None = None


class CupBase(SQLModel):
    date_time: datetime
    username: str
    coffee_id: int = Field(foreign_key="coffee.id")


class Cup(CupBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

    coffee: Coffee | None = Relationship(back_populates="cups")


class CupUpdate(CupBase):
    date_time: datetime | None = None
    username: str | None = None
    coffee_id: int | None = None


class User(SQLModel):
    username: str
