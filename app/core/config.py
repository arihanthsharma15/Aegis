from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()


class Settings(BaseModel):
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    RATE_LIMIT: int = int(os.getenv("RATE_LIMIT", 60))
    WINDOW_SIZE: int = int(os.getenv("WINDOW_SIZE", 60))


settings = Settings()
