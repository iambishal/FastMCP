"""Configuration management module for environment-specific settings."""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings with validation - all values from environment variables."""
    
    # Application
    app_name: str = Field(
        default="Indy-mcp-server",
        description="Application name",
        json_schema_extra={"env": "APP_NAME"}
    )
    app_version: str = Field(
        default="1.0.0",
        description="Application version",
        json_schema_extra={"env": "APP_VERSION"}
    )
    
    # Server
    host: str = Field(
        default="0.0.0.0",
        description="Server host",
        json_schema_extra={"env": "SERVER_HOST"}
    )
    port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Server port",
        json_schema_extra={"env": "SERVER_PORT"}
    )
    workers: int = Field(
        default=4,
        ge=1,
        description="Number of worker processes",
        json_schema_extra={"env": "SERVER_WORKERS"}
    )
    
    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        json_schema_extra={"env": "LOG_LEVEL"}
    )
    log_file: str = Field(
        default="logs/app.log",
        description="Log file path",
        json_schema_extra={"env": "LOG_FILE"}
    )
    log_max_bytes: int = Field(
        default=10485760,
        description="Max log file size in bytes",
        json_schema_extra={"env": "LOG_MAX_BYTES"}
    )
    log_backup_count: int = Field(
        default=5,
        description="Number of backup log files",
        json_schema_extra={"env": "LOG_BACKUP_COUNT"}
    )
    
    # Application Insights
    applicationinsights_connection_string: str | None = Field(
        default=None,
        description="Azure Application Insights connection string",
        json_schema_extra={"env": "APPLICATIONINSIGHTS_CONNECTION_STRING"}
    )
    enable_telemetry: bool = Field(
        default=False,
        description="Enable Application Insights telemetry",
        json_schema_extra={"env": "ENABLE_TELEMETRY"}
    )
    
    # Performance
    request_timeout: int = Field(
        default=30,
        ge=1,
        description="Request timeout in seconds",
        json_schema_extra={"env": "REQUEST_TIMEOUT"}
    )
    max_connections: int = Field(
        default=1000,
        ge=1,
        description="Maximum concurrent connections",
        json_schema_extra={"env": "MAX_CONNECTIONS"}
    )
    rate_limit_requests: int = Field(
        default=100,
        ge=1,
        description="Rate limit requests per minute",
        json_schema_extra={"env": "RATE_LIMIT_REQUESTS"}
    )
    
    # External APIs Configuration - Global Settings
    api_timeout: int = Field(
        default=30,
        ge=1,
        description="Global API timeout in seconds (applies to all external APIs)",
        json_schema_extra={"env": "API_TIMEOUT"}
    )
    api_max_retries: int = Field(
        default=3,
        ge=0,
        description="Global API max retries (applies to all external APIs)",
        json_schema_extra={"env": "API_MAX_RETRIES"}
    )
    
    # External API Endpoints
    petstore_base_url: str = Field(
        default="https://petstore.swagger.io/v2",
        description="Petstore API base URL",
        json_schema_extra={"env": "PETSTORE_BASE_URL"}
    )
    
    jsonplaceholder_base_url: str = Field(
        default="https://jsonplaceholder.typicode.com",
        description="JSON Placeholder API base URL",
        json_schema_extra={"env": "JSONPLACEHOLDER_BASE_URL"}
    )
    
    # Security
    enable_auth: bool = Field(
        default=False,
        description="Enable JWT authentication",
        json_schema_extra={"env": "ENABLE_AUTH"}
    )
    jwt_jwks_uri: str | None = Field(
        default=None,
        description="JWKS URI for JWT verification",
        json_schema_extra={"env": "JWT_JWKS_URI"}
    )
    jwt_issuer: str | None = Field(
        default=None,
        description="JWT token issuer",
        json_schema_extra={"env": "JWT_ISSUER"}
    )
    jwt_audience: str | None = Field(
        default=None,
        description="JWT token audience",
        json_schema_extra={"env": "JWT_AUDIENCE"}
    )
    
    # CORS
    cors_origins: list[str] = Field(
        default=["*"],
        description="Allowed CORS origins (comma-separated)",
        json_schema_extra={"env": "CORS_ORIGINS"}
    )
    cors_allow_credentials: bool = Field(
        default=True,
        description="Allow CORS credentials",
        json_schema_extra={"env": "CORS_ALLOW_CREDENTIALS"}
    )
    
    # Health Check
    health_check_interval: int = Field(
        default=30,
        ge=5,
        description="Health check interval in seconds",
        json_schema_extra={"env": "HEALTH_CHECK_INTERVAL"}
    )
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v_upper
    
    @property
    def apis(self) -> dict:
        """
        Build APIs configuration dict from individual environment variables.
        Uses global timeout and max_retries for all APIs.
        
        Returns:
            dict: API configurations for APIManager
        """
        return {
            "petstore": {
                "base_url": self.petstore_base_url,
                "timeout": self.api_timeout,
                "max_retries": self.api_max_retries,
                "description": "Petstore API for pet management"
            },
            "jsonplaceholder": {
                "base_url": self.jsonplaceholder_base_url,
                "timeout": self.api_timeout,
                "max_retries": self.api_max_retries,
                "description": "JSON Placeholder for testing"
            }
        }
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"
        # Use environment variables with the specified names
        populate_by_name = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Returns:
        Settings: Application settings singleton
    """
    return Settings()


# Export singleton instance
settings = get_settings()
