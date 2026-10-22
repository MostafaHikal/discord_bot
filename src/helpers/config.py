from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str
    APP_VERSION: str
    DISCORD_PUBLIC_KEY: str
    DISCORD_APPLICATION_ID: str
    DISCORD_BOT_TOKEN: str
    DISCORD_GUILD_ID: str
    DATABASE_URL: str

    model_config = SettingsConfigDict(env_file=".env")


def get_settings() -> Settings:
    return Settings()