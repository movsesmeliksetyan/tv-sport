from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime config, overridable via env vars (see .env.example)."""

    model_config = SettingsConfigDict(env_prefix="PTV_", env_file=".env")

    # Source
    base_url: str = "https://www.pimpletv.ru"
    request_timeout_s: float = 25.0
    user_agent: str = (
        "Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )

    # Scheduler cadence
    listing_refresh_seconds: int = 180          # 2-5 min per PRD FR-3
    stream_window_minutes: int = 75             # resolve streams within this of kickoff
    stream_refresh_seconds: int = 60            # how often to re-check live-window matches

    # Behavior
    mock_mode: bool = True                      # serve canned sample data until the crawler lands (Phase 1)
    timezone: str = "Europe/Moscow"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000


settings = Settings()
