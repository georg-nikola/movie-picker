from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from database import get_db, init_db
from models import User, WatchedMovie
from auth import hash_password, verify_password, create_jwt, get_current_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Movie Picker API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://movie-picker.georg-nikola.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Schemas ───────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class WatchedMovieRequest(BaseModel):
    movie_title: str


# ── Auth endpoints ────────────────────────────────────────────────────────────

@app.post("/api/auth/register", status_code=201)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    if len(req.username) < 3:
        raise HTTPException(status_code=422, detail="Username must be at least 3 characters")

    result = await db.execute(select(User).where(User.username == req.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Username already taken")

    if len(req.password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters")

    user = User(username=req.username, password=hash_password(req.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)

    jwt_token = create_jwt(str(user.id))
    return {"token": jwt_token, "username": user.username}


@app.post("/api/auth/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == req.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    jwt_token = create_jwt(str(user.id))
    return {"token": jwt_token, "username": user.username}


# ── Watched movies endpoints ──────────────────────────────────────────────────

@app.get("/api/watched")
async def get_watched(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(WatchedMovie.movie_title).where(WatchedMovie.user_id == current_user.id)
    )
    return {"watched": [row[0] for row in result.fetchall()]}


@app.post("/api/watched", status_code=201)
async def add_watched(
    req: WatchedMovieRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(WatchedMovie).where(
            WatchedMovie.user_id == current_user.id,
            WatchedMovie.movie_title == req.movie_title,
        )
    )
    if existing.scalar_one_or_none():
        return {"message": "Already in watched list"}

    watched = WatchedMovie(user_id=current_user.id, movie_title=req.movie_title)
    db.add(watched)
    await db.commit()
    return {"message": "Added to watched list"}


@app.delete("/api/watched/{movie_title}", status_code=204)
async def remove_watched(
    movie_title: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WatchedMovie).where(
            WatchedMovie.user_id == current_user.id,
            WatchedMovie.movie_title == movie_title,
        )
    )
    watched = result.scalar_one_or_none()
    if not watched:
        raise HTTPException(status_code=404, detail="Not found in watched list")
    await db.delete(watched)
    await db.commit()


# ── Account management ────────────────────────────────────────────────────────

@app.delete("/api/users/me", status_code=204)
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete the authenticated user's account and all their data."""
    await db.delete(current_user)
    await db.commit()
    return Response(status_code=204)


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok"}
