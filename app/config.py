"""Typed runtime settings for the Exhibit A backend."""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Runtime configuration resolved from environment variables."""

    database_path: Path = Path("data/exhibit-a.db")
    host: str = "127.0.0.1"
    port: int = 8001
    debug: bool = False

    apns_key_id: str = ""
    apns_team_id: str = ""
    apns_key_path: str = ""
    apns_use_sandbox: bool = False

    admin_key_hash: str = ""
