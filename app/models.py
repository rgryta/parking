from __future__ import annotations
import datetime
from sqlalchemy import Integer, String, Boolean, Date, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Space(Base):
    __tablename__ = "spaces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    description: Mapped[str | None] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    reservations: Mapped[list["Reservation"]] = relationship(
        "Reservation", back_populates="space", cascade="all, delete-orphan"
    )


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    space_id: Mapped[int] = mapped_column(Integer, ForeignKey("spaces.id"))
    reserver_name: Mapped[str] = mapped_column(String(100))
    date: Mapped[datetime.date] = mapped_column(Date)
    note: Mapped[str | None] = mapped_column(Text)

    space: Mapped["Space"] = relationship("Space", back_populates="reservations")
