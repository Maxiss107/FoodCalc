from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class AppConfig(BaseSettings):
    DEBUG: bool = True
    SECRET_KEY: str = "django-insecure-dev-key"
    ALLOWED_HOSTS: str = "localhost,127.0.0.1"

    POSTGRES_DB: str = "foodcalc"
    POSTGRES_USER: str = "foodcalc_user"
    POSTGRES_PASSWORD: str = "foodcalc_pass"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    CORS_ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def allowed_hosts_list(self) -> list[str]:
        return [host.strip() for host in self.ALLOWED_HOSTS.split(",") if host.strip()]

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]


config = AppConfig()