import random
import json


def create_empty_board(size=10):
    return [[0.0] * size for _ in range(size)]


def can_place_ship(board, x, y, length, orientation):
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

    if orientation == 'horizontal':
        if y + length > len(board):
            return False
        for i in range(length):
            if board[x][y + i] != 0:
                return False
            for dx, dy in directions:
                nx, ny = x + dx, y + i + dy
                if 0 <= nx < len(board) and 0 <= ny < len(board) and board[nx][ny] != 0:
                    return False
    elif orientation == 'vertical':
        if x + length > len(board):
            return False
        for i in range(length):
            if board[x + i][y] != 0:
                return False
            for dx, dy in directions:
                nx, ny = x + i + dx, y + dy
                if 0 <= nx < len(board) and 0 <= ny < len(board) and board[nx][ny] != 0:
                    return False
    return True


def place_ship(board, x, y, length, orientation,num):
    if orientation == 'horizontal':
        for i in range(length):
            board[x][y + i] = length + (num/10)
    elif orientation == 'vertical':
        for i in range(length):
            board[x + i][y] = length + (num/10)


def generate_board():
    board = create_empty_board()
    ships = [(1, 4), (2, 3), (3, 2), (4, 1)]  # (length, count)
    for length, count in ships:
        for num in range(count):
            placed = False
            while not placed:
                orientation = random.choice(['horizontal', 'vertical'])
                x = random.randint(0, len(board) - 1)
                y = random.randint(0, len(board) - 1)
                if can_place_ship(board, x, y, length, orientation):
                    place_ship(board, x, y, length, orientation, num+1)
                    placed = True
    return board


def board_to_json(board):
    return json.dumps(board)