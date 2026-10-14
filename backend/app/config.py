from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "TCL WorkHub"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://tcl_workhub:change-me@postgres:5432/tcl_workhub"
    keycloak_issuer_url: str = "http://keycloak:8080/realms/tcl-workhub"
    backend_cors_origins: str = "http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

