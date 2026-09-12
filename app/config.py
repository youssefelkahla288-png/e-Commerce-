"""
config.py — the ONE place the whole project reads its settings from.

Why centralize this?
  - The API key and file paths are needed in several files.
  - If they're scattered, changing one means hunting through the codebase.
  - Here, everything reads `settings.something`. Change it once, fixed everywhere.
"""

import os
from pathlib import Path
from dataclasses import dataclass

from dotenv import load_dotenv

# BASE_DIR = the project root (the folder that contains app/, scripts/, etc.)
# __file__ is THIS file (app/config.py); .parent is app/; .parent.parent is the root.
BASE_DIR = Path(__file__).resolve().parent.parent

# Read the .env file at the project root and load its values into the environment.
load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)  # frozen=True => settings can't be accidentally changed at runtime
class Settings:
    # The secret key, read from the environment. Default "" so the app doesn't crash on import;
    # we check for it where it's actually used.
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

    # Absolute paths, built from the project root so they work no matter where you run from.
    db_path: str = str(BASE_DIR / "ecommerce.db")
    schema_path: str = str(BASE_DIR / "schema.json")
    vectorstore_dir: str = str(BASE_DIR / "data" / "vectorstore")


# One shared instance the rest of the project imports: `from app.config import settings`
settings = Settings()