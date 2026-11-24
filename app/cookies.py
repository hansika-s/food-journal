from fastapi import Response

from app.config import COOKIE_SECURE, SESSION_EXPIRE_DAYS

SESSION_COOKIE = "session_id"


# Sets the session cookie. HttpOnly keeps JavaScript from reading it.
def set_session_cookie(response: Response, session_id: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE,
        value=session_id,
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
        max_age=SESSION_EXPIRE_DAYS * 24 * 60 * 60,
    )


def delete_session_cookie(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE)
