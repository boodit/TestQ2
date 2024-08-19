from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.auth import router as authRouter
from src.game import router as gameRouter

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:8000/players/login",
    "http://localhost:8000/players",
    "http://localhost:8000",
    "null"
]
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(authRouter)
app.include_router(gameRouter)



