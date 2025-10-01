from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routers import auth_router, game_router, base_router

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:8000/players/login",
    "http://localhost:8000/players",
    "http://localhost:8000",
    "null",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    from src.game import websockets_list
    from src.database.orm import AsyncORM
    from src.game import ConnectionManager
    import json

    games = await AsyncORM.get_all_play_game()
    for game in games:
        manager = ConnectionManager(
            game.first_player_id,
            game.second_player_id,
            game.id,
            json.loads(game.first_player_board),
            json.loads(game.second_player_board),
        )
        websockets_list.append(manager)

    print(f"Restored {len(websockets_list)} active games")

    yield

    print("Application shutting down...")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(game_router)
app.include_router(base_router)
