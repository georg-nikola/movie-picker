from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from pydantic import BaseModel, EmailStr
import uuid

from config import settings
from database import get_db, init_db
from models import User, OtpToken, WatchedMovie
from auth import hash_password, verify_password, generate_otp, create_jwt, get_current_user
from email_service import send_otp_email


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
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class VerifyRequest(BaseModel):
    email: EmailStr
    code: str


class WatchedMovieRequest(BaseModel):
    movie_title: str


# ── Auth endpoints ────────────────────────────────────────────────────────────

async def _create_and_send_otp(user: User, db: AsyncSession) -> None:
    # Invalidate old tokens
    await db.execute(delete(OtpToken).where(OtpToken.user_id == user.id))

    code = settings.test_otp_code if settings.test_otp_code else generate_otp()
    token = OtpToken(
        user_id=user.id,
        code=code,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
    )
    db.add(token)
    await db.commit()
    await send_otp_email(user.email, code)


@app.post("/api/auth/register", status_code=201)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    if len(req.password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters")

    user = User(email=req.email, password=hash_password(req.password))
    db.add(user)
    await db.flush()
    await _create_and_send_otp(user, db)
    return {"message": "Verification code sent to your email"}


@app.post("/api/auth/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    await _create_and_send_otp(user, db)
    return {"message": "Verification code sent to your email"}


@app.post("/api/auth/verify")
async def verify(req: VerifyRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    now = datetime.now(timezone.utc)
    token_result = await db.execute(
        select(OtpToken).where(
            OtpToken.user_id == user.id,
            OtpToken.code == req.code,
            OtpToken.used == False,
            OtpToken.expires_at > now,
        )
    )
    token = token_result.scalar_one_or_none()
    if not token:
        raise HTTPException(status_code=401, detail="Invalid or expired code")

    token.used = True
    user.verified = True
    await db.commit()

    jwt_token = create_jwt(str(user.id))
    return {"token": jwt_token, "email": user.email}


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


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok"}
