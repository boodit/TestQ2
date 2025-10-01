import os

from fastapi import status, Response
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm
from starlette.responses import FileResponse

from src.game import websockets_list, ConnectionManager, update_game
from src.schemas import PlayerCreateDTO, AnswerTokenDTO, AnswerDTO, AnswerPlayerListDTO
from src.security import settings, create_access_token

from src.auth import (
    authenticate_player,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

import json

from fastapi import APIRouter, Depends, HTTPException, WebSocket, Query
from starlette.websockets import WebSocketDisconnect

from src.database.models import Player
from src.database.orm import AsyncORM
from src.auth import get_current_player
from src.handler import (
    mask_board_for_self,
    mask_board_for_opponent,
)
from src.schemas import GameDTO, GameStatsDTO
from src.database.models import Active

game_router = APIRouter(
    prefix="/games",
    tags=["game"],
)


auth_router = APIRouter(
    prefix="/players",
    tags=["auth"],
)

base_router = APIRouter(
    tags=["base"],
)


@auth_router.post("/register", response_model=AnswerDTO)
async def register_player(player: PlayerCreateDTO):
    db_player = await AsyncORM.get_player(username=player.username)
    if db_player:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "data": None,
                "details": "Username already registered",
            },
        )
    await AsyncORM.add_player(username=player.username, password=player.password)
    return {"status": "success", "data": None, "details": "Пользователь упешно создан"}


@auth_router.post("/login", response_model=AnswerTokenDTO)
async def login_for_access_token(
    response: Response, form_data: OAuth2PasswordRequestForm = Depends()
):
    player = await authenticate_player(
        username=form_data.username, password=form_data.password
    )
    if not player:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": "error",
                "data": None,
                "details": "Incorrect username or password",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": player.username}, expires_delta=access_token_expires
    )
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="strict",
    )
    return {
        "status": "success",
        "data": {
            "username": player.username,
            "access_token": access_token,
            "token_type": "bearer",
        },
        "details": "Пользователь упешно вошел",
    }


@auth_router.get("/", response_model=AnswerPlayerListDTO)
async def get_players_non_game():
    res = await AsyncORM.get_free_players()
    return {
        "status": "success",
        "data": res,
        "details": "Список не играющих пользователей",
    }


@game_router.get("/")
async def get_games():
    value = await AsyncORM.get_active_game_room()
    games = [GameDTO.model_validate(val, from_attributes=True) for val in value]
    return {"status": "success", "data": games, "details": "Game created successfully"}


@game_router.get("/{game_id}/state")
async def game_state(
    game_id: int, current_player: Player = Depends(get_current_player)
):
    cm = next((cm for cm in websockets_list if cm.game_id == game_id), None)
    if not cm:
        game = await AsyncORM.get_game_by_id(game_id)
        if not game:
            raise HTTPException(404, "Game not found")
        cm = ConnectionManager(
            game.first_player_id,
            game.second_player_id,
            game.id,
            json.loads(game.first_player_board),
            json.loads(game.second_player_board),
        )
    role = "first" if current_player.id == cm.white_list[0] else "second"
    return {
        "status": "success",
        "data": {
            "role": role,
            "current_turn": cm.current_turn,
            "my_view": mask_board_for_self(
                cm.first_player_board if role == "first" else cm.second_player_board
            ),
            "opponent_view": mask_board_for_opponent(
                cm.second_player_board if role == "first" else cm.first_player_board
            ),
        },
    }


@game_router.websocket("/{game_id}/play")
async def websocket_endpoint(
    websocket: WebSocket, game_id: int, token: str = Query(None)
):
    current_player = await get_current_player(access_token=token)
    if current_player is None:
        await websocket.accept()
        await websocket.close(code=1008, reason="Authentication failed")
        return

    connection_manager = next(
        (cm for cm in websockets_list if cm.game_id == game_id), None
    )
    if not connection_manager:
        await websocket.accept()
        await websocket.close(code=1008, reason="Game not found")
        return

    try:
        await connection_manager.connect(websocket, current_player.id)
    except Exception:
        if websocket.client_state.name != "DISCONNECTED":
            await websocket.close(code=1011, reason="Internal server error")
        return

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            await update_game(connection_manager, data, current_player.id, websocket)
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
        await AsyncORM.update_player_status(current_player.id, Active.out_game)
    except Exception:
        connection_manager.disconnect(websocket)


@game_router.get("/{player_id}/stats")
async def player_stats(player_id: int):
    value = await AsyncORM.get_games_for_player_id(player_id)
    games = [GameStatsDTO.model_validate(val, from_attributes=True) for val in value]
    return {
        "status": "success",
        "data": games,
        "details": f"Player id:{player_id} games",
    }


@game_router.post("/up_all_game")
async def up_all_game():
    games = await AsyncORM.get_all_play_game()
    if len(games) == 0:
        raise HTTPException(
            status_code=400,
            detail={"status": "success", "data": None, "details": "Game not found"},
        )
    for game in games:
        new_game = ConnectionManager(
            game.first_player_id,
            game.second_player_id,
            game.id,
            json.loads(game.first_player_board),
            json.loads(game.second_player_board),
        )
        websockets_list.append(new_game)
    return {
        "status": "success",
        "data": [game.game_id for game in websockets_list],
        "details": "Games upped successfully",
    }


@game_router.post("/create")
async def create_game(
    second_player_username: str, current_player: Player = Depends(get_current_player)
):
    second_player = await AsyncORM.get_player(second_player_username)
    if not second_player:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "success",
                "data": None,
                "details": "Second player not found",
            },
        )
    second_player_id = second_player[0].id
    new_game = await AsyncORM.create_game_room(
        first_player_id=current_player.id, second_player_id=second_player_id
    )
    connection_manager = ConnectionManager(
        current_player.id,
        second_player_id,
        new_game["insert_id"],
        json.loads(new_game["first_player_board"]),
        json.loads(new_game["second_player_board"]),
    )
    websockets_list.append(connection_manager)
    return {
        "status": "success",
        "data": {"game_id": new_game["insert_id"]},
        "details": "Game created successfully",
    }


@base_router.get("/play")
async def play_index():
    return FileResponse(os.path.join(settings.WEB_ROOT, "main.html"))
