from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MediSlot API"
    app_version: str = "1.0.0"
    database_url: str = "postgresql+psycopg://medislot:medislot@localhost:5432/medislot"
    # Comma-separated list of allowed browser origins (only needed when the
    # frontend is not served through the same Nginx/Ingress host).
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
