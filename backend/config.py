from sqlalchemy import URL
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_username: str
    db_password: str
    pg_host: str
    pg_database: str

    @computed_field
    @property
    def db_url(self) -> URL:
        return URL.create(
            "postgresql+psycopg",
            username=self.db_username,
            password=self.db_password,
            host=self.pg_host,
            database=self.pg_database,
        )

    # Extracty specific settings
    discord_webhook_url: str
    r2_secret_access_key: str
    r2_access_key_id: str
    r2_account_id: str
    assets_bucket: str = "espresso-assets-dev"  # TODO: Replace with {ENVIRONMENT}
    proxy_network_url: str

    @computed_field
    @property
    def r2_endpoint_url(self) -> str:
        return f"https://{self.r2_account_id}.r2.cloudflarestorage.com"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf8",
    )


settings = Settings()
