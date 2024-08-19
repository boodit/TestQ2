import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException, WebSocket, Query
from starlette.websockets import WebSocketDisconnect, WebSocketState

from src.database.models import Player
from src.database.orm import AsyncORM
from src.auth import get_current_player
from src.schemas import GameDTO, GameStatsDTO
from src.database.models import Active

router = APIRouter(
    prefix="/games",
    tags=["game"],
)


def is_last_part_of_ship(grid, row, col, ship_type):
    def is_within_bounds(r, c):
        return 0 <= r < len(grid) and 0 <= c < len(grid[0])

    def mark_around(r, c):
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if is_within_bounds(nr, nc) and grid[nr][nc] == 0.0:
                grid[nr][nc] = 'M'

    def get_ship_parts(r, c, ship_type):
        parts = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            while is_within_bounds(nr, nc) and grid[nr][nc] in {ship_type, 'S'}:
                parts.append((nr, nc))
                nr += dr
                nc += dc
        return parts

    # Проверка на корректность координат и типа корабля
    if not is_within_bounds(row, col) or grid[row][col] != ship_type:
        return False

    ship_length = int(str(ship_type).split('.')[0])
    parts = get_ship_parts(row, col, ship_type)

    # Проверка, что количество частей корабля соответствует его длине
    if len(parts) + 1 != ship_length:
        return False

    # Проверка, что все части корабля поражены
    all_hit = all(grid[r][c] == 'S' for r, c in parts)

    if all_hit:
        # Помечаем текущую ячейку как пораженную часть корабля
        grid[row][col] = 'S'
        for r, c in parts:
            grid[r][c] = 'S'
            mark_around(r, c)
        mark_around(row, col)
        return True

    return False


def are_all_ships_destroyed(grid):
    def is_within_bounds(r, c):
        return 0 <= r < len(grid) and 0 <= c < len(grid[0])

    def find_ship(r, c):
        ship_type = grid[r][c]
        if ship_type == 0.0 or ship_type == 'S' or ship_type == 'M':
            return None
        parts = [(r, c)]
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            while is_within_bounds(nr, nc) and grid[nr][nc] == ship_type:
                parts.append((nr, nc))
                nr += dr
                nc += dc
        return parts

    def is_ship_destroyed(parts):
        return all(grid[r][c] == 'S' for r, c in parts)

    def mark_as_checked(parts):
        for r, c in parts:
            grid[r][c] = 'M'  # Mark as checked to avoid reprocessing

    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c] != 0.0 and grid[r][c] != 'S' and grid[r][c] != 'M':
                ship_parts = find_ship(r, c)
                if ship_parts:
                    if not is_ship_destroyed(ship_parts):
                        return False
                    mark_as_checked(ship_parts)

    return True


def create_empty_board(size=10):
    return [[None] * size for _ in range(size)]


class ConnectionManager:
    def __init__(self, first_player_id: int, second_player_id: int, game_id: int,
                 first_player_board, second_player_board):
        self.game_id = game_id
        self.white_list = (first_player_id, second_player_id)
        self.active_connections: List[WebSocket] = []
        self.first_player_board = first_player_board
        self.second_player_board = second_player_board

    async def connect(self, websocket: WebSocket, player_id: int):
        print(f"Player ID: {player_id}")

        await websocket.accept()
        if len(self.active_connections) >= 2 or player_id not in self.white_list:
            print("Connection rejected")
            print(f'Connection count: {len(self.active_connections)}')
            await websocket.close(4000)
            return
        self.active_connections.append(websocket)
        try:
            await AsyncORM.update_player_status(player_id, Active.in_game)
            if len(self.active_connections) == 1:
                await websocket.send_json({
                    "status": "success",
                    "data": {
                        "init_message": True,
                        "player": "first"
                    },
                    "details": "First connect"
                })
            else:
                await websocket.send_json({
                    "status": "success",
                    "data": {
                        "init_message": True,
                        "player": "second"
                    },
                    "details": "Second connect"
                })
                if self.active_connections[1].application_state == WebSocketState.CONNECTED:
                    await self.active_connections[1].send_json({
                        "status": "success",
                        "data": {
                            "init_message": True,
                            "player": "second"
                        },
                        "details": "Your turn!"
                    })
        except Exception as e:
            print(f"Error sending message: {e}")
            await websocket.close(1011)
            self.disconnect(websocket)

        print(f"Active connections: {self.active_connections}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)


    def disconnectAll(self):
        self.active_connections = []

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_json(message)


websockets_list = []


async def update_game(manager: ConnectionManager, data, websocket: WebSocket):
    cell_number = int(data["cell"]) - 1
    row, col = cell_number // 10, cell_number % 10
    if data["player"] == "first":
        board = manager.second_player_board
        player = manager.white_list[0]
    else:
        board = manager.first_player_board
        player = manager.white_list[1]
    #Обработка хода
    if type(board[row][col]) == str:
        data['message'] = "Uncorrected cell"
    elif board[row][col] == 0.0:
        board[row][col] = "M"
        data['message'] = "miss"
        await AsyncORM.update_board_in_game(manager.game_id, manager.first_player_board,
                                            manager.second_player_board)
    elif board[row][col] != 0.0:
        check = is_last_part_of_ship(board, row, col, board[row][col])
        if not check:
            data['message'] = board[row][col]
            board[row][col] = "S"
            await AsyncORM.update_board_in_game(manager.game_id, manager.first_player_board,
                                                manager.second_player_board)
        else:
            data['message'] = f"{board[row][col]}/D"
            await AsyncORM.update_board_in_game(manager.game_id, manager.first_player_board,
                                                manager.second_player_board)
            await AsyncORM.change_game_end(manager.game_id, player)
    if are_all_ships_destroyed(board):
        data["message"] = "win"
    await manager.broadcast(data)
    if data["message"] == "win":
        manager.disconnectAll()


@router.post("/create")
async def create_game(second_player_username: str, current_player: Player = Depends(get_current_player)):
    second_player = await AsyncORM.get_player(second_player_username)
    if not second_player:
        raise HTTPException(status_code=400, detail={
            "status": "success",
            "data": None,
            "details": "Second player not found"
        })
    second_player_id = second_player[0].id
    new_game = await AsyncORM.create_game_room(first_player_id=current_player.id,
                                               second_player_id=second_player_id)
    connection_manager = ConnectionManager(current_player.id, second_player_id,
                                           new_game['insert_id'],
                                           json.loads(new_game['first_player_board']),
                                           json.loads(new_game['second_player_board']))
    websockets_list.append(connection_manager)
    return {
        "status": "success",
        "data": {"game_id": new_game['insert_id']},
        "details": "Game created successfully"
    }


@router.post("/up_all_game")
async def up_all_game():
    games = await AsyncORM.get_all_play_game()
    if len(games) == 0:
        raise HTTPException(status_code=400, detail={
            "status": "success",
            "data": None,
            "details": "Game not found"
        })
    for game in games:
        new_game = ConnectionManager(game.first_player_id, game.second_player_id, game.id,
                                     json.loads(game.first_player_board), json.loads(game.second_player_board))
        websockets_list.append(new_game)
    return {
        "status": "success",
        "data": [game.game_id for game in websockets_list],
        "details": "Games upped successfully"
    }


@router.get("/")
async def get_games():
    value = await AsyncORM.get_active_game_room()
    games = [GameDTO.model_validate(val, from_attributes=True) for val in value]
    return {
        "status": "success",
        "data": games,
        "details": "Game created successfully"
    }


@router.websocket("/{game_id}/play")
async def websocket_endpoint(websocket: WebSocket, game_id: int, token: str = Query(None)):
    current_player = await get_current_player(access_token=token)
    print(f"Current player: {current_player}, Token: {token}")
    connection_manager_o = None
    if current_player is None:
        await websocket.accept()
        await websocket.close(code=1008, reason="Authentication failed")
        return

    try:
        connection_manager = next((cm for cm in websockets_list if cm.game_id == game_id), None)
        if connection_manager:
            print(f"Connecting to game {game_id} for player {current_player.id}")
            connection_manager_o = connection_manager
            await connection_manager.connect(websocket, current_player.id)
        else:
            print(f"Game {game_id} not found for player {current_player.id}")
            await websocket.close(code=1008, reason="Game not found")
    except Exception as e:
        print(f"Error: {e}")
        await websocket.close(code=1011, reason="Internal server error")
    try:
        while True:
            data = await websocket.receive_text()
            data = json.loads(data)
            await update_game(connection_manager_o, data, websocket)
    except WebSocketDisconnect:
        connection_manager_o.disconnect(websocket)
        await AsyncORM.update_player_status(current_player.id, Active.out_game)
        print(f'Disconnect :"{websocket}')
    except Exception as e:
        print(f"Error: {e}")


@router.get("/{player_id}/stats")
async def player_stats(player_id: int):
    value = await AsyncORM.get_games_for_player_id(player_id)
    print(type(value))
    games = [GameStatsDTO.model_validate(val, from_attributes=True) for val in value]
    return {
        "status": "success",
        "data": games,
        "details": f"Player id:{player_id} games"
    }
