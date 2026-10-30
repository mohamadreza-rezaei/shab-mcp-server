from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    shab_api_base_url: str = Field(default="https://api.shab.ir", alias="SHAB_API_BASE_URL")
    shab_api_lang: str = Field(default="fa", alias="SHAB_API_LANG")
    shab_api_version: str = Field(default="v_1_4", alias="SHAB_API_VERSION")
    # Non-stateful Origin so OTP verify returns Sanctum access_token (not SPA cookie session).
    shab_api_origin: str = Field(default="https://shab-mcp.internal", alias="SHAB_API_ORIGIN")
    shab_api_platform: str = Field(default="mcp", alias="SHAB_API_PLATFORM")
    shab_web_base_url: str = Field(default="https://www.shab.ir", alias="SHAB_WEB_BASE_URL")
    # Callers: OfficeAPIClient, .env.example. Affected: backoffice Client-Id header.
    # User: Implement the plan as specified.
    shab_backoffice_client_id: str = Field(
        default="78fse4gc-q2ed-8fnh-sewq-bgnc8rtwjaer",
        alias="SHAB_BACKOFFICE_CLIENT_ID",
    )
    shab_mcp_surface: str = Field(default="all", alias="SHAB_MCP_SURFACE")

    shab_connect_timeout: float = Field(default=5.0, alias="SHAB_CONNECT_TIMEOUT")
    shab_read_timeout: float = Field(default=20.0, alias="SHAB_READ_TIMEOUT")
    shab_max_retries: int = Field(default=2, alias="SHAB_MAX_RETRIES")

    shab_mcp_host: str = Field(default="0.0.0.0", alias="SHAB_MCP_HOST")
    shab_mcp_port: int = Field(default=8000, alias="SHAB_MCP_PORT")
    shab_mcp_transport: str = Field(default="http", alias="SHAB_MCP_TRANSPORT")

    @property
    def api_prefix(self) -> str:
        base = self.shab_api_base_url.rstrip("/")
        return f"{base}/api/{self.shab_api_lang}/sandbox/{self.shab_api_version}"

    @property
    def backoffice_prefix(self) -> str:
        base = self.shab_api_base_url.rstrip("/")
        return f"{base}/api/{self.shab_api_lang}/{self.shab_api_version}/backoffice"


@lru_cache
def get_settings() -> Settings:
    return Settings()
