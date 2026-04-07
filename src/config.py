"""Configuration management with environment variables."""

from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field
import yaml
from pathlib import Path


class Settings(BaseSettings):
    """Application settings."""
    
    # Server configuration
    server_name: str = "Farshad Enterprise MCP Server"
    server_version: str = "2.0.0"
    environment: str = Field(default="development", pattern="^(development|staging|production)$")
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR)$")
    
    # Database
    database_url: str = Field(default="sqlite+aiosqlite:///./mcp_data.db")
    database_pool_size: int = 10
    database_max_overflow: int = 20
    
    # Redis cache
    redis_url: Optional[str] = None
    cache_ttl: int = 300
    
    # Security
    api_key: Optional[str] = None
    jwt_secret: Optional[str] = None
    allowed_origins: List[str] = Field(default_factory=lambda: ["*"])
    
    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_period: int = 60
    
    # Features
    enable_semantic_search: bool = True
    enable_backups: bool = True
    backup_interval_hours: int = 24
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def load_yaml_config(self, config_path: Path):
        """Load configuration from YAML file."""
        if config_path.exists():
            with open(config_path) as f:
                yaml_config = yaml.safe_load(f)
                if not yaml_config:
                    return
                for key, value in yaml_config.items():
                    if hasattr(self, key):
                        setattr(self, key, value)


settings = Settings()

# Load environment-specific config
env_config = Path(f"config/{settings.environment}.yaml")
if env_config.exists():
    settings.load_yaml_config(env_config)