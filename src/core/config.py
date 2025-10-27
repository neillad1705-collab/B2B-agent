from pydantic_settings import BaseSettings
from pathlib import Path
from enum import Enum
from typing import Optional, List


class Settings(BaseSettings):
    SQLALCHEMY_HOST: str = "127.0.0.1"
    SQLALCHEMY_PORT: int = 6379
    SQLALCHEMY_USER: str = "root"
    SQLALCHEMY_PASSWORD: Optional[str] = None
    

settings = Settings()
