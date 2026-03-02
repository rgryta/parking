import os
from contextlib import asynccontextmanager
from datetime import date, timedelta
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, init_db
from app import crud
from app.schemas import SpaceCreate, SpaceUpdate, ReservationCreate
from app.auth import (
    create_token, check_password, check_admin_password,
    get_current_user, require_auth, require_admin, AuthRedirect,
)

BASE_DIR = os.path.dirname(__file__)
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Parking Reservation", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")


@app.exception_handler(AuthRedirect)
async def auth_redirect_handler(request: Request, exc: AuthRedirect):
    return RedirectResponse(exc.url, status_code=302)


# --- Auth ---

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = "", next: str = ""):
    if get_current_user(request):
        return RedirectResponse("/")
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": error,
        "next": next,
    })


@app.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    next: str = Form(""),
):
    is_admin = check_admin_password(password)
    is_user = check_password(password)

    if not is_admin and not is_user:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid password.",
            "next": next,
        }, status_code=401)

    token = create_token(username.strip() or "User", is_admin=is_admin)
    redirect_to = f"/{next}" if next else "/"
    response = RedirectResponse(redirect_to, status_code=303)
    response.set_cookie(
        "session", token,
        httponly=True, samesite="lax",
        max_age=8 * 3600,
    )
    return response


@app.post("/logout")
async def logout():
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie("session")
    return response


# --- Main reservation view ---

@app.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    start: str = "",
    db: AsyncSession = Depends(get_db),
):
    user = require_auth(request)

    try:
        start_date = date.fromisoformat(start) if start else date.today()
    except ValueError:
        start_date = date.today()

    # Show 14 days
    days = [start_date + timedelta(days=i) for i in range(14)]
    end_date = days[-1]

    spaces = await crud.get_spaces(db)
    reservations = await crud.get_reservations_in_range(db, start_date, end_date)

    # Build lookup: (space_id, date) -> reservation
    res_map = {(r.space_id, r.date): r for r in reservations}

    prev_start = (start_date - timedelta(days=14)).isoformat()
    next_start = (start_date + timedelta(days=14)).isoformat()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "user": user,
        "spaces": spaces,
        "days": days,
        "res_map": res_map,
        "start_date": start_date.isoformat(),
        "prev_start": prev_start,
        "next_start": next_start,
    })


# --- Reservation actions ---

@app.post("/reserve")
async def reserve(
    request: Request,
    space_id: int = Form(...),
    res_date: str = Form(...),
    reserver_name: str = Form(...),
    note: str = Form(""),
    start: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    require_auth(request)
    try:
        d = date.fromisoformat(res_date)
    except ValueError:
        raise HTTPException(400, "Invalid date")

    data = ReservationCreate(
        space_id=space_id,
        reserver_name=reserver_name.strip() or "Anonymous",
        date=d,
        note=note.strip() or None,
    )
    await crud.create_reservation(db, data)
    redirect = f"/?start={start}" if start else "/"
    return RedirectResponse(redirect, status_code=303)


@app.post("/cancel/{reservation_id}")
async def cancel(
    reservation_id: int,
    request: Request,
    start: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    user = require_auth(request)
    reservation = await crud.get_reservation(db, reservation_id)
    if not reservation:
        raise HTTPException(404, "Not found")

    # Only admin or the original reserver can cancel
    if not user.get("admin") and reservation.reserver_name != user["sub"]:
        raise HTTPException(403, "Not authorized")

    await crud.delete_reservation(db, reservation_id)
    redirect = f"/?start={start}" if start else "/"
    return RedirectResponse(redirect, status_code=303)


# --- Admin ---

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = require_admin(request)
    spaces = await crud.get_spaces(db, include_inactive=True)
    reservations = await crud.get_all_reservations(db)

    # Build space lookup for reservation display
    space_map = {s.id: s for s in spaces}

    return templates.TemplateResponse("admin.html", {
        "request": request,
        "user": user,
        "spaces": spaces,
        "reservations": reservations,
        "space_map": space_map,
    })


@app.post("/admin/spaces/add")
async def admin_add_space(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    require_admin(request)
    await crud.create_space(db, SpaceCreate(name=name.strip(), description=description.strip() or None))
    return RedirectResponse("/admin", status_code=303)


@app.post("/admin/spaces/{space_id}/toggle")
async def admin_toggle_space(
    space_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    require_admin(request)
    space = await crud.get_space(db, space_id)
    if space:
        await crud.update_space(db, space_id, SpaceUpdate(is_active=not space.is_active))
    return RedirectResponse("/admin", status_code=303)


@app.post("/admin/spaces/{space_id}/delete")
async def admin_delete_space(
    space_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    require_admin(request)
    await crud.delete_space(db, space_id)
    return RedirectResponse("/admin", status_code=303)


@app.post("/admin/reservations/{reservation_id}/delete")
async def admin_delete_reservation(
    reservation_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    require_admin(request)
    await crud.delete_reservation(db, reservation_id)
    return RedirectResponse("/admin", status_code=303)
