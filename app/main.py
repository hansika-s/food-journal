from fastapi import FastAPI

from app.routers import auth, places, posts, users

app = FastAPI(title="Food Journal")

app.include_router(auth.router)
app.include_router(posts.router)
app.include_router(users.router)
app.include_router(places.router)
