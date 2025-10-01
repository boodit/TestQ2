from fastapi import Cookie, HTTPException
import jwt
from starlette import status

from src.security import verify_password, settings, ALGORITHM

from src.database.orm import AsyncORM


# JWT
ACCESS_TOKEN_EXPIRE_MINUTES = 30


async def authenticate_player(username: str, password: str):
    player = await AsyncORM.get_player(username)
    if not player:
        return False
    if not verify_password(password, player[0].hashed_password):
        return False
    return player[0]


async def get_current_player(access_token: str = Cookie(None)):
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    player = await AsyncORM.get_player(username=username)
    if player is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return player[0]
