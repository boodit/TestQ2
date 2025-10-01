def mask_board_for_self(board):
    # Возвращаем как есть: свои корабли + 'S'/'M'
    return board


def mask_board_for_opponent(board):
    # Для соперника скрываем корабли: оставляем только 'S'/'M' и None/0.0
    masked = []
    for row in board:
        mr = []
        for cell in row:
            if isinstance(cell, str):
                # 'S' или 'M' остаются
                mr.append(cell)
            elif cell == 0.0:
                mr.append(0.0)
            else:
                # части корабля (например 3.1) скрываем как 0.0
                mr.append(0.0)
        masked.append(mr)
    return masked


def is_last_part_of_ship(grid, row, col, ship_type):
    def is_within_bounds(r, c):
        return 0 <= r < len(grid) and 0 <= c < len(grid[0])

    def mark_around(r, c):
        directions = [
            (-1, -1),
            (-1, 0),
            (-1, 1),
            (0, -1),
            (0, 1),
            (1, -1),
            (1, 0),
            (1, 1),
        ]
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if is_within_bounds(nr, nc) and grid[nr][nc] == 0.0:
                grid[nr][nc] = "M"

    def get_ship_parts(r, c, ship_type):
        parts = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            while is_within_bounds(nr, nc) and grid[nr][nc] in {ship_type, "S"}:
                parts.append((nr, nc))
                nr += dr
                nc += dc
        return parts

    if not is_within_bounds(row, col) or grid[row][col] != ship_type:
        return False

    ship_length = int(str(ship_type).split(".")[0])
    parts = get_ship_parts(row, col, ship_type)
    if len(parts) + 1 != ship_length:
        return False

    all_hit = all(grid[r][c] == "S" for r, c in parts)

    if all_hit:
        grid[row][col] = "S"
        for r, c in parts:
            grid[r][c] = "S"
            mark_around(r, c)
        mark_around(row, col)
        return True

    return False


def are_all_ships_destroyed(grid):
    def is_within_bounds(r, c):
        return 0 <= r < len(grid) and 0 <= c < len(grid[0])

    def find_ship(r, c):
        ship_type = grid[r][c]
        if ship_type == 0.0 or ship_type == "S" or ship_type == "M":
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
        return all(grid[r][c] == "S" for r, c in parts)

    def mark_as_checked(parts):
        for r, c in parts:
            grid[r][c] = "M"

    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c] != 0.0 and grid[r][c] != "S" and grid[r][c] != "M":
                ship_parts = find_ship(r, c)
                if ship_parts:
                    if not is_ship_destroyed(ship_parts):
                        return False
                    mark_as_checked(ship_parts)

    return True
