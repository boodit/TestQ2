from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
import jwt
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm

from src.database.models import Player
from src.schemas import PlayerCreateDTO, AnswerTokenDTO, AnswerDTO, AnswerPlayerListDTO
from src.database.orm import AsyncORM
from src.security import verify_password, settings, ALGORITHM, create_access_token

#JWT
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Инициализация роутера
router = APIRouter(
    prefix="/players",
    tags=["auth"],
)


async def authenticate_player(username: str, password: str):
    player = await AsyncORM.get_player(username)
    if not player:
        return False
    if not verify_password(password, player[0].hashed_password):
        return False
    return player[0]


async def get_current_player(access_token: str = Cookie(None)):
    # credentials_exception = HTTPException(
    #     status_code=status.HTTP_401_UNAUTHORIZED,
    #     detail="Could not validate credentials",
    #     headers={"WWW-Authenticate": "Bearer"},
    # )
    if not access_token:
        print("Эти ошибки не обрабатывается вебсокетом")
        return None
    username: str = None
    try:
        payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            # raise credentials_exception
            print("Эти ошибки не обрабатывается вебсокетом")
            return None
    except jwt.PyJWTError:
        # raise credentials_exception
        print("Эти ошибки не обрабатывается вебсокетом")
    player = await AsyncORM.get_player(username=username)
    if player is None:
        # raise credentials_exception
        print("Эти ошибки не обрабатывается вебсокетом")
        return None
    return player[0]


@router.post("/register", response_model=AnswerDTO)
async def register_player(player: PlayerCreateDTO):
    db_player = await AsyncORM.get_player(username=player.username)
    if db_player:
        raise HTTPException(
            status_code=400,
            detail=
            {
                "status": "error",
                "data": None,
                "details": 'Username already registered'
            }
        )
    await AsyncORM.add_player(username=player.username, password=player.password)
    return {
        "status": "success",
        "data": None,
        "details": "Пользователь упешно создан"
    }


@router.post("/login", response_model=AnswerTokenDTO)
async def login_for_access_token(response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    player = await authenticate_player(username=form_data.username, password=form_data.password)
    if not player:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=
            {
                "status": "error",
                "data": None,
                "details": "Incorrect username or password"
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": player.username}, expires_delta=access_token_expires)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="strict",
    )
    return {
        "status": "success",
        "data":
            {
                "username": player.username,
                "access_token": access_token,
                "token_type": "bearer"
            },
        "details": "Пользователь упешно вошел"
    }


@router.get("/", response_model=AnswerPlayerListDTO)
async def get_players_non_game():
    res = await AsyncORM.get_free_players()
    return {
        "status": "success",
        "data": res,
        "details": "Список не играющих пользователей"
    }
