from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Search order: root .env (local dev from backend/) → backend/.env → env vars (Docker)
    model_config = SettingsConfigDict(
        env_file=["../.env", ".env"],
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API Security
    api_secret_key: str = "change-me-in-production"

    # AI
    gemini_api_key: str = ""

    # Email (Gmail SMTP)
    gmail_user: str = ""
    gmail_app_password: str = ""

    # CORS
    allowed_origins: str = "http://localhost:3000"

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


settings = Settings()
