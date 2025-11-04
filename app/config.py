import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class AppConfig:
    api_base_url: str = os.getenv("API_BASE_URL", "http://localhost:4000")

CONFIG = AppConfig()
