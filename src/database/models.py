import datetime
import enum
from typing import Optional

from sqlalchemy import (
    ForeignKey,
    Integer,
    String,
    Boolean,
)
from sqlalchemy.dialects.postgresql import JSONB

from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.database import Base


class Active(enum.Enum):
    in_game = "in_game"
    out_game = "out_game"


class Player(Base):
    __tablename__ = 'player'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    hashed_password: Mapped[str]
    active: Mapped[Active]

    games_one_id: Mapped[list['Game']] = relationship(
        back_populates="player_one_id",
        foreign_keys="Game.first_player_id",
    )
    games_two_id: Mapped[list['Game']] = relationship(
        back_populates="player_two_id",
        foreign_keys="Game.second_player_id",
    )


class Game(Base):
    __tablename__ = 'game'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_player_id: Mapped[int] = mapped_column(Integer, ForeignKey('player.id', ondelete='CASCADE'))
    second_player_id: Mapped[int] = mapped_column(Integer, ForeignKey('player.id', ondelete='CASCADE'))
    first_player_board: Mapped[JSONB] = mapped_column(JSONB)
    second_player_board: Mapped[JSONB] = mapped_column(JSONB)
    game_end: Mapped[bool] = mapped_column(Boolean, default=False)
    winner_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('player.id', ondelete='CASCADE'))
    end_data: Mapped[Optional[datetime.datetime]]

    player_one_id: Mapped['Player'] = relationship(
        back_populates="games_one_id",
        foreign_keys=[first_player_id],
    )
    player_two_id: Mapped['Player'] = relationship(
        back_populates='games_two_id',
        foreign_keys=[second_player_id],
    )
