import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    HOST: str
    PORT: int

    BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
    WEB_ROOT: str = os.path.join(BASE_DIR, "templates")

    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    SECRET_KEY: str

    @property
    def DATABASE_URL_asyncpg(self):
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def DATABASE_URL_psycopg(self):
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def SECRET_KEY(self):
        return self.SECRET_KEY

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
