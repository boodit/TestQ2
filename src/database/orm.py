from datetime import datetime

from sqlalchemy import select, delete, update
from sqlalchemy.orm import selectinload

from src.database.database import async_session, async_engine
from src.database.models import *
from src.security import get_password_hash
from src.board_create import generate_board, board_to_json


class AsyncORM:
    @staticmethod
    async def create_tables():
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

    @staticmethod
    async def get_player(username: str):
        async with async_session() as session:
            query = (
                select(Player)
                .filter_by(username=username)
            )
            res = await session.execute(query)
            result = res.scalars().all()
            return result

    @staticmethod
    async def add_player(username: str, password: str):
        async with async_session() as session:
            hashed_password = get_password_hash(password)
            new_player = Player(username=username, hashed_password=hashed_password, active=Active.out_game)
            session.add(new_player)
            await session.commit()

    @staticmethod
    async def remove_player(username: str):
        async with async_session() as session:
            stmt = delete(Player).where(Player.username == username)
            await session.execute(stmt)
            await session.commit()

    @staticmethod
    async def get_free_players():
        async with async_session() as session:
            query = (
                select(Player.username).
                where(Player.active == Active.out_game)
                .limit(30)
            )
            res = await session.execute(query)
            result = res.scalars().all()
            return result

    @staticmethod
    async def create_game_room(first_player_id: int, second_player_id: int):
        async with async_session() as session:
            first_player_board = board_to_json(generate_board())
            second_player_board = board_to_json(generate_board())
            new_game_room = Game(first_player_id=first_player_id, second_player_id=second_player_id,
                                 first_player_board=first_player_board, second_player_board=second_player_board)
            session.add(new_game_room)
            await session.flush()
            insert_id = new_game_room.id
            await session.commit()
            return {
                'insert_id': insert_id,
                'first_player_board': first_player_board,
                'second_player_board': second_player_board
            }

    @staticmethod
    async def get_active_game_room():
        async with async_session() as session:
            query = (
                select(Game)
                .where(Game.game_end == False)
                .limit(30)
            )
            res = await session.execute(query)
            result = res.scalars().all()
            return result

    @staticmethod
    async def get_all_games_player(player_id: int):
        async with async_session() as session:
            pass

    @staticmethod
    async def get_all_play_game():
        async with async_session() as session:
            query = (
                select(Game)
                .where(Game.game_end == False)
            )
            res = await session.execute(query)
            result = res.scalars().all()
            return result

    @staticmethod
    async def get_game_by_id(game_id: int):
        async with async_session() as session:
            query = (
                select(Game)
                .where(Game.id == game_id)
            )
            res = await session.execute(query)
            result = res.scalars().all()
            return result

    @staticmethod
    async def update_board_in_game(game_id: int, first_player_board: list, second_player_board: list):
        async with async_session() as session:
            json_first_player_board = board_to_json(first_player_board)
            json_second_player_board = board_to_json(second_player_board)
            stmt = (
                update(Game)
                .values(first_player_board=json_first_player_board, second_player_board=json_second_player_board)
                .where(Game.id == game_id)
            )
            await session.execute(stmt)
            await session.commit()
            return True

    @staticmethod
    async def change_game_end(game_id: int, player_id: int):
        async with async_session() as session:
            stmt = (
                update(Game)
                .values(game_end=True, winner_id=player_id, end_data=datetime.utcnow())
                .where(Game.id == game_id)
            )
            await session.execute(stmt)
            await session.commit()
            return True

    @staticmethod
    async def get_games_for_player_id(player_id: int):
        async with async_session() as session:
            result = []
            query = (
                select(Player)
                .options(selectinload(Player.games_one_id))
                .where(Player.id == player_id)
            )
            res = await session.execute(query)
            res = res.unique().scalars().all()
            if not result:
                [result.append(val) for val in res[0].games_one_id]
            query = (
                select(Player)
                .options(selectinload(Player.games_two_id))
                .where(Player.id == player_id)
            )
            res = await session.execute(query)
            res = res.unique().scalars().all()
            if not result:
                [result.append(val) for val in res[0].games_two_id]
            return result

    @staticmethod
    async def update_player_status(player_id: int, status: Active = Active.out_game):
        async with async_session() as session:
            stmt = (
                update(Player)
                .values(active=status)
                .where(Player.id == player_id)
            )
            await session.execute(stmt)
            await session.commit()
            return True
