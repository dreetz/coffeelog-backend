from datetime import datetime, date

from pydantic import BaseModel


class User(BaseModel):
    username: str

class CoffeeBase(BaseModel):
    roasting_facility: str
    coffee_name: str
    size_g: int
    roast_date: date | None
    open_date: date | None
    price: float | None
    country_of_origin: str | None


class Coffee(CoffeeBase):
    id: int | None


class CoffeeUpdate(CoffeeBase):
    roasting_facility: str | None = None
    coffee_name: str | None = None
    size_g: int | None = None
    roast_date: date | None = None
    open_date: date | None = None
    price: float | None = None
    country_of_origin: str | None = None


class CupBase(BaseModel):
    date_time: datetime
    username: str
    coffee_id: int


class Cup(CupBase):
    id: int | None

    coffee: Coffee | None


class CupUpdate(CupBase):
    date_time: datetime | None = None
    username: str | None = None
    coffee_id: int | None = None



