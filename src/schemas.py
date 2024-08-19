import datetime

from pydantic import BaseModel, JsonValue


class AnswerDTO(BaseModel):
    status: str
    data: dict | None = None
    details: str


class TokenDTO(BaseModel):
    username: str
    access_token: str
    token_type: str


class AnswerTokenDTO(AnswerDTO):
    data: "TokenDTO"


class TokenDataDTO(BaseModel):
    username: str | None = None


class PlayerDTO(BaseModel):
    username: str


class PlayerCreateDTO(PlayerDTO):
    password: str


class AnswerPlayerListDTO(AnswerDTO):
    data: list


class PlayerInDBDTO(PlayerCreateDTO):
    hashed_password: str


class GameCreateDTO(BaseModel):
    second_player_username: str


class GameDTO(BaseModel):
    id: int
    first_player_id: int
    second_player_id: int
    first_player_board: JsonValue
    second_player_board: JsonValue
    game_end: bool
    winner_id: int | None = None
    end_data: datetime.datetime | None = None


class GameListDTO(BaseModel):
    game_list: list["GameDTO"]


class GameStatsDTO(BaseModel):
    id: int
    first_player_id: int
    second_player_id: int
    game_end: bool
    winner_id: int | None = None
    end_data: datetime.datetime | None = None


class GameStatsListDTO(BaseModel):
    game_stats: list["GameStatsDTO"]
