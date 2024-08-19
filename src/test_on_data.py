import json
import os
import sys
from typing import List

sys.path.insert(1, os.path.join(sys.path[0], '..'))

from src.database.orm import AsyncORM
import asyncio
from src.security import settings
from src.board_create import board_to_json,generate_board

async def main():
    #await AsyncORM().add_player(username="Bob", password="<PASSWORD>")
    #await AsyncORM().remove_player(username="Bob")
    # player = await AsyncORM().get_player(username="Bob")
    # board = generate_board()
    # for row in board:
    #
    #     print(row, end="\n")
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

    def check_win(grid):
        for col in grid:
            for cell in col:
                if not (cell in ["M", "S"] or cell == 0.0):
                        return False
        return True

    #___________________________________________________

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


    # Пример использования
    field = [
        [0.0, 2.3, 2.3, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.4],
        [0.0, 0.0, 4.1, 4.1, "S", "S", 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.2, 0.0, 0.0],
        [0.0, 1.3, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 3.1, 3.1, 3.1, 0.0, 3.2, 0.0, 0.0],
        [1.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 3.2, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 3.2, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 2.1, 2.1, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 2.2, 2.2]
    ]

    field2 = [
        [0.0, "S", "S", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, "S"],
        [0.0, 0.0, "S", "S", "S", "S", 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, "S", 0.0, 0.0],
        [0.0, "S", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, "S", "S", "S", 0.0, "S", 0.0, 0.0],
        ["S", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, "S", 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, "S", 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, "S", "S", 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, "S", "S"]
    ]

    print(are_all_ships_destroyed(field2))
    # Печать обновленного поля
    # for row in field:
    #     print(row)


asyncio.run(main())