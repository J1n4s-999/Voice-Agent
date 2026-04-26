from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Voice Agent API"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    database_url: str
    admin_secret: str

    token_secret: str
    token_salt: str = "email-confirm"
    token_max_age_seconds: int = 1800

    public_base_url: str = "http://localhost:8000"
    webhook_shared_secret: str

    google_credentials_path: str | None = None
    google_service_account_json: str | None = None
    google_calendar_id: str = "primary"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    postmark_server_token: str
    email_from: str

    google_oauth_client_id: str
    google_oauth_client_secret: str
    google_oauth_redirect_uri: str


settings = Settings()