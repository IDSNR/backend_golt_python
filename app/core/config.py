import os
from dataclasses import dataclass
from typing import List

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str = "partnerhub-python-backend"
    port: int = int(os.getenv("PORT", "8000"))
    frontend_origins: List[str] = None

    def __post_init__(self):
        if self.frontend_origins is None:
            raw = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
            object.__setattr__(self, "frontend_origins", [origin.strip() for origin in raw.split(",") if origin.strip()])


settings = Settings()
