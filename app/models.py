from datetime import datetime, date

from sqlalchemy import ForeignKey, MetaData
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_`%(constraint_name)s`",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


class Coffee(Base):
    __tablename__ = "coffeelog_coffee"

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
    __tablename__ = "coffeelog_cup"

    id: Mapped[int] = mapped_column(primary_key=True)
    date_time: Mapped[datetime]
    username: Mapped[str]
    coffee_id: Mapped[int] = mapped_column(ForeignKey("coffeelog_coffee.id"))

    coffee: Mapped["Coffee"] = relationship(back_populates="cups")
