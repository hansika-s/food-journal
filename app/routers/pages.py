from pathlib import Path

from fastapi import APIRouter, Request, Form, Depends, Cookie, HTTPException, status
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from app.config import COOKIE_SECURE, SESSION_EXPIRE_DAYS
from app.database import get_db
from app.dependencies import csrf_matches, get_current_web_session
from app.models import User, UserSession
from app.schemas.users import UserCreate
from app.security import hash_password
from app.services import sessions
from app.services.auth import authenticate_user

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")


@router.get("/login")
def show_login_form(request: Request):
    return templates.TemplateResponse(request, "login.html", {"error": None})


@router.post("/login")
def submit_login_form(
    request: Request,
    email: str = Form(),
    password: str = Form(),
    db: Session = Depends(get_db),
):
    db_user = authenticate_user(db, email, password)
    if db_user is None:
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": "Invalid email or password"},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    session_id = sessions.create_session(db, db_user.id)

    response = RedirectResponse(url="/posts", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
        max_age=SESSION_EXPIRE_DAYS * 24 * 60 * 60,
    )
    return response


@router.get("/signup")
def show_signup_form(request: Request):
    return templates.TemplateResponse(request, "signup.html", {"error": None})


@router.post("/signup")
def submit_signup_form(
    request: Request,
    name: str = Form(),
    email: str = Form(),
    password: str = Form(),
    db: Session = Depends(get_db),
):
    try:
        user_data = UserCreate(name=name, email=email, password=password)
    except ValidationError as error:
        return templates.TemplateResponse(
            request,
            "signup.html",
            {"error": error.errors()[0]["msg"]},
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )

    db.add(User(email=user_data.email.lower(), password_hash=hash_password(user_data.password), name=user_data.name))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return templates.TemplateResponse(
            request,
            "signup.html",
            {"error": "Email already registered"},
            status_code=status.HTTP_409_CONFLICT,
        )

    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/logout")
def submit_logout_form(
    csrf_token: str | None = Form(default=None),
    session_id: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if session_id is not None:
        user_session = sessions.get_session(db, session_id)
        if user_session is not None and not csrf_matches(user_session.csrf_token, csrf_token):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token missing or invalid")
        sessions.delete_session(db, session_id)

    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("session_id")

    return response


@router.get("/posts")
def show_posts_page(
    request: Request,
    user_session: UserSession = Depends(get_current_web_session),
):
    return templates.TemplateResponse(request, "posts.html", {"csrf_token": user_session.csrf_token})
