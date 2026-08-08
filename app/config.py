from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    data_provider: str = "mock"
    provider_fallback: str | None = "baostock"
    watchlist: str = "600519,000858,601318"
    database_path: str = "data/app.db"
    ifind_api_key: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def watchlist_codes(self) -> list[str]:
        return [code.strip() for code in self.watchlist.split(",") if code.strip()]


settings = Settings()
