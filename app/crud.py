from datetime import date
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Space, Reservation
from app.schemas import SpaceCreate, SpaceUpdate, ReservationCreate


# --- Spaces ---

async def get_spaces(db: AsyncSession, include_inactive: bool = False) -> list[Space]:
    q = select(Space)
    if not include_inactive:
        q = q.where(Space.is_active == True)  # noqa: E712
    q = q.order_by(Space.name)
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_space(db: AsyncSession, space_id: int) -> Space | None:
    result = await db.execute(select(Space).where(Space.id == space_id))
    return result.scalar_one_or_none()


async def create_space(db: AsyncSession, data: SpaceCreate) -> Space:
    space = Space(name=data.name, description=data.description)
    db.add(space)
    await db.commit()
    await db.refresh(space)
    return space


async def update_space(db: AsyncSession, space_id: int, data: SpaceUpdate) -> Space | None:
    space = await get_space(db, space_id)
    if not space:
        return None
    for field, val in data.model_dump(exclude_none=True).items():
        setattr(space, field, val)
    await db.commit()
    await db.refresh(space)
    return space


async def delete_space(db: AsyncSession, space_id: int) -> bool:
    space = await get_space(db, space_id)
    if not space:
        return False
    await db.delete(space)
    await db.commit()
    return True


# --- Reservations ---

async def get_reservations_in_range(
    db: AsyncSession, start: date, end: date
) -> list[Reservation]:
    result = await db.execute(
        select(Reservation).where(
            and_(Reservation.date >= start, Reservation.date <= end)
        )
    )
    return list(result.scalars().all())


async def get_reservation(db: AsyncSession, reservation_id: int) -> Reservation | None:
    result = await db.execute(select(Reservation).where(Reservation.id == reservation_id))
    return result.scalar_one_or_none()


async def get_existing_reservation(
    db: AsyncSession, space_id: int, date: date
) -> Reservation | None:
    result = await db.execute(
        select(Reservation).where(
            and_(Reservation.space_id == space_id, Reservation.date == date)
        )
    )
    return result.scalar_one_or_none()


async def get_user_reservation_on_date(
    db: AsyncSession, reserver_name: str, date: date
) -> Reservation | None:
    result = await db.execute(
        select(Reservation).where(
            and_(Reservation.reserver_name == reserver_name, Reservation.date == date)
        )
    )
    return result.scalar_one_or_none()


async def create_reservation(db: AsyncSession, data: ReservationCreate) -> Reservation | None:
    existing = await get_existing_reservation(db, data.space_id, data.date)
    if existing:
        return None
    reservation = Reservation(
        space_id=data.space_id,
        reserver_name=data.reserver_name,
        date=data.date,
        note=data.note,
    )
    db.add(reservation)
    await db.commit()
    await db.refresh(reservation)
    return reservation


async def delete_reservation(db: AsyncSession, reservation_id: int) -> bool:
    reservation = await get_reservation(db, reservation_id)
    if not reservation:
        return False
    await db.delete(reservation)
    await db.commit()
    return True


async def get_all_reservations(db: AsyncSession) -> list[Reservation]:
    result = await db.execute(select(Reservation).order_by(Reservation.date))
    return list(result.scalars().all())
