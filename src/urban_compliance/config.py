"""Application settings loaded from environment variables."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the API and background components."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="UC_",
        extra="ignore",
    )

    app_name: str = "Urban Compliance AI"
    data_dir: Path = Path("./data")
    database_url: str = "sqlite:///./data/urban_compliance.db"
    max_upload_mb: int = 50

    def ensure_dirs(self) -> None:
        """Create the local data directories used by the application."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "uploads").mkdir(parents=True, exist_ok=True)


settings = Settings()