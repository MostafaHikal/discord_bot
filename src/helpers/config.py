from pydantic_settings import BaseSettings, SettingsConfigDict

# Single source of truth for configuration: every setting the app needs is declared and validated here,
# so the rest of the code never reads environment variables directly.

class Settings(BaseSettings):
    """
    Typed app configuration, read from environment variables or `.env`.
    * Every field is required, so a missing value fails at startup, not mid-request.
    * Secrets live only in the environment, never in code.
    """
    
    APP_NAME: str
    APP_VERSION: str
    DISCORD_PUBLIC_KEY: str
    DISCORD_APPLICATION_ID: str
    DISCORD_BOT_TOKEN: str
    DISCORD_GUILD_ID: str
    DATABASE_URL: str
    TEST_DATABASE_URL: str | None = None

    model_config = SettingsConfigDict(env_file=".env")


# Used through `Depends(get_settings)`; building a fresh instance each call lets tests override it easily.
def get_settings() -> Settings:
    return Settings()