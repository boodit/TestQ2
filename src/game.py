from typing import List

from fastapi import WebSocket
from starlette.websockets import WebSocketState

from src.database.orm import AsyncORM
from src.handler import (
    mask_board_for_self,
    mask_board_for_opponent,
    is_last_part_of_ship,
    are_all_ships_destroyed,
)
from src.database.models import Active


class ConnectionManager:
    def __init__(
        self,
        first_player_id: int,
        second_player_id: int,
        game_id: int,
        first_player_board,
        second_player_board,
    ):
        self.game_id = game_id
        self.white_list = (first_player_id, second_player_id)
        self.active_connections: List[WebSocket] = []
        self.first_player_board = first_player_board
        self.second_player_board = second_player_board
        self.current_turn: str | None = None

    async def connect(self, websocket: WebSocket, player_id: int):
        old_connection = None
        for conn in self.active_connections:
            if hasattr(conn, "player_id") and conn.player_id == player_id:
                old_connection = conn
                break

        if old_connection:
            self.disconnect(old_connection)

        if len(self.active_connections) >= 2:
            await websocket.accept()
            await websocket.close(code=1008, reason="Game full")
            return

        if player_id not in self.white_list:
            await websocket.accept()
            await websocket.close(code=1008, reason="Player not allowed")
            return

        await websocket.accept()
        websocket.player_id = player_id
        self.active_connections.append(websocket)

        await AsyncORM.update_player_status(player_id, Active.in_game)
        role = "first" if player_id == self.white_list[0] else "second"

        if len(self.active_connections) == 1:
            await websocket.send_json(
                {
                    "status": "success",
                    "data": {"init_message": True, "player": "first"},
                    "details": "First connect",
                }
            )
        else:
            await websocket.send_json(
                {
                    "status": "success",
                    "data": {"init_message": True, "player": "second"},
                    "details": "Second connect",
                }
            )
            if self.current_turn is None:
                self.current_turn = "second"
            if self.active_connections[0].application_state == WebSocketState.CONNECTED:
                await self.active_connections[0].send_json(
                    {
                        "status": "success",
                        "data": {"message": "opponent_joined", "your_turn": False},
                        "details": "Opponent joined",
                    }
                )

        snapshot = {
            "type": "state",
            "data": {
                "role": role,
                "current_turn": self.current_turn,
                "my_view": mask_board_for_self(
                    self.first_player_board
                    if role == "first"
                    else self.second_player_board
                ),
                "opponent_view": mask_board_for_opponent(
                    self.second_player_board
                    if role == "first"
                    else self.first_player_board
                ),
            },
        }
        await websocket.send_json(snapshot)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    def disconnectAll(self):
        self.active_connections = []

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)


websockets_list = []


async def push_state_to_all(manager: ConnectionManager):
    for conn in list(manager.active_connections):
        role = (
            "first"
            if getattr(conn, "player_id", None) == manager.white_list[0]
            else "second"
        )
        payload = {
            "type": "state",
            "data": {
                "role": role,
                "current_turn": manager.current_turn,
                "my_view": mask_board_for_self(
                    manager.first_player_board
                    if role == "first"
                    else manager.second_player_board
                ),
                "opponent_view": mask_board_for_opponent(
                    manager.second_player_board
                    if role == "first"
                    else manager.first_player_board
                ),
            },
        }
        await conn.send_json(payload)


async def update_game(manager: ConnectionManager, data, shooter_id: int, ws: WebSocket):
    role = "first" if shooter_id == manager.white_list[0] else "second"
    if manager.current_turn and manager.current_turn != role:
        await ws.send_json({"type": "error", "message": "not_your_turn"})
        return

    cell_number = int(data["cell"]) - 1
    row, col = cell_number // 10, cell_number % 10
    if not (0 <= row < 10 and 0 <= col < 10):
        await ws.send_json({"type": "error", "message": "out_of_bounds"})
        return

    board = (
        manager.second_player_board if role == "first" else manager.first_player_board
    )

    sunk_now = False
    if isinstance(board[row][col], str):
        msg = "Uncorrected cell"
    elif board[row][col] == 0.0:
        board[row][col] = "M"
        msg = "miss"
        await AsyncORM.update_board_in_game(
            manager.game_id, manager.first_player_board, manager.second_player_board
        )
    else:
        sunk = is_last_part_of_ship(board, row, col, board[row][col])
        if not sunk:
            msg = board[row][col]
            board[row][col] = "S"
            await AsyncORM.update_board_in_game(
                manager.game_id, manager.first_player_board, manager.second_player_board
            )
        else:
            msg = f"{board[row][col]}/D"
            sunk_now = True
            await AsyncORM.update_board_in_game(
                manager.game_id, manager.first_player_board, manager.second_player_board
            )
            # если у вас здесь была логика финала, оставьте по необходимости
            # await AsyncORM.change_game_end(manager.game_id, shooter_id)

    if are_all_ships_destroyed(board):
        msg = "win"

    out = {"type": "shot", "cell": data["cell"], "player": role, "message": msg}
    await manager.broadcast(out)

    if msg == "miss":
        manager.current_turn = "second" if role == "first" else "first"
    elif sunk_now and msg != "win":
        manager.current_turn = "second" if role == "first" else "first"
        await push_state_to_all(manager)

    if msg == "win":
        await push_state_to_all(manager)
        manager.disconnectAll()
