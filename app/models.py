from datetime import datetime, date

from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Coffee(Base):
    __tablename__ = "coffee"

    id: Mapped[int] = mapped_column(primary_key=True)
    roasting_facility: Mapped[str]
    coffee_name: Mapped[str]
    size_g: Mapped[int]
    roast_date: Mapped[date | None]
    open_date: Mapped[date | None]
    price: Mapped[float | None]
    country_of_origin: Mapped[str | None]

    cups: Mapped[list["Cup"]] = relationship(
        back_populates="coffee",
    )


class Cup(Base):
    __tablename__ = "cup"

    id: Mapped[int] = mapped_column(primary_key=True)
    date_time: Mapped[datetime]
    username: Mapped[str]
    coffee_id: Mapped[int] = mapped_column(ForeignKey("coffee.id"))

    coffee: Mapped["Coffee"] = relationship(back_populates="cups")
