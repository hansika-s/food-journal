from fastapi import FastAPI, Request, status
from fastapi.responses import RedirectResponse

from app.dependencies import LoginRequiredError
from app.routers import auth, posts, users, pages

app = FastAPI(title="Food Journal")


@app.exception_handler(LoginRequiredError)
def redirect_to_login(request: Request, exc: LoginRequiredError) -> RedirectResponse:
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


app.include_router(auth.router)
app.include_router(posts.router)
app.include_router(users.router)
app.include_router(pages.router)
