from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "TCL WorkHub"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://tcl_workhub:change-me@postgres:5432/tcl_workhub"
    keycloak_public_issuer_url: str = "http://localhost:8080/realms/tcl-workhub"
    keycloak_internal_url: str = "http://keycloak:8080"
    keycloak_realm: str = "tcl-workhub"
    keycloak_backend_client_id: str = "tcl-workhub-api"
    backend_cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]

    @property
    def keycloak_jwks_url(self) -> str:
        return (
            f"{self.keycloak_internal_url.rstrip('/')}/realms/{self.keycloak_realm}"
            "/protocol/openid-connect/certs"
        )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

