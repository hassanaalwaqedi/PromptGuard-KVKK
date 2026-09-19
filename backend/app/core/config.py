"""Centralized runtime configuration loaded from environment variables."""

from dataclasses import dataclass
import os

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "PromptGuard-KVKK API")
    app_env: str = os.getenv("APP_ENV", "development")
    api_v1_prefix: str = os.getenv("API_V1_PREFIX", "/api/v1")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./promptguard.db")
    frontend_url: str = os.getenv(
        "FRONTEND_URL",
        "http://localhost:3000,https://promptguard-kvkk.web.app",
    )

    @property
    def frontend_origins(self) -> list[str]:
        """Configured origins plus explicit local-development loopback aliases."""
        origins = [origin.strip() for origin in self.frontend_url.split(",") if origin.strip()]
        if self.app_env == "development":
            origins.extend(
                [
                    "http://127.0.0.1:3000",
                    "http://localhost:3100",
                    "http://127.0.0.1:3100",
                ]
            )
        return list(dict.fromkeys(origins))


settings = Settings()
