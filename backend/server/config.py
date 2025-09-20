# server/config.py
"""
Configuration management for the SIEM AI Agent.
Handles environment variables, settings validation, and configuration loading.
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from pathlib import Path


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Uses Pydantic for validation and type conversion.
    """
    
    # === API Configuration ===
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_reload: bool = Field(default=False, env="API_RELOAD")
    api_log_level: str = Field(default="info", env="API_LOG_LEVEL")
    
    # === Elasticsearch Configuration ===
    elasticsearch_host: str = Field(default="http://localhost:9200", env="ELASTICSEARCH_HOST")
    elasticsearch_username: Optional[str] = Field(default=None, env="ELASTICSEARCH_USERNAME")
    elasticsearch_password: Optional[str] = Field(default=None, env="ELASTICSEARCH_PASSWORD")
    elasticsearch_verify_certs: bool = Field(default=False, env="ELASTICSEARCH_VERIFY_CERTS")
    elasticsearch_timeout: int = Field(default=30, env="ELASTICSEARCH_TIMEOUT")
    elasticsearch_max_retries: int = Field(default=3, env="ELASTICSEARCH_MAX_RETRIES")
    elasticsearch_backup_hosts: List[str] = Field(default=[], env="ELASTICSEARCH_BACKUP_HOSTS")
    
    # === SIEM Data Configuration ===
    force_mock_data: bool = Field(default=False, env="FORCE_MOCK_DATA")
    mock_data_file: str = Field(default="mock_siem_data.json", env="MOCK_DATA_FILE")
    
    # === NLP Configuration ===
    nlp_model_type: str = Field(default="mock", env="NLP_MODEL_TYPE")
    nlp_model_path: str = Field(default="./models", env="NLP_MODEL_PATH")
    nlp_confidence_threshold: float = Field(default=0.7, env="NLP_CONFIDENCE_THRESHOLD")
    
    # === Context Management ===
    max_sessions: int = Field(default=1000, env="MAX_SESSIONS")
    session_timeout_hours: int = Field(default=24, env="SESSION_TIMEOUT_HOURS")
    context_history_size: int = Field(default=10, env="CONTEXT_HISTORY_SIZE")
    
    # === Security Configuration ===
    api_key_header: str = Field(default="X-API-Key", env="API_KEY_HEADER")
    allowed_origins: List[str] = Field(default=["*"], env="ALLOWED_ORIGINS")
    enable_cors: bool = Field(default=True, env="ENABLE_CORS")
    
    # === Logging Configuration ===
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="structured", env="LOG_FORMAT")
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")
    enable_file_logging: bool = Field(default=False, env="ENABLE_FILE_LOGGING")
    
    # === Report Configuration ===
    report_max_events: int = Field(default=1000, env="REPORT_MAX_EVENTS")
    report_cache_ttl_minutes: int = Field(default=30, env="REPORT_CACHE_TTL_MINUTES")
    enable_report_caching: bool = Field(default=True, env="ENABLE_REPORT_CACHING")
    
    # === Performance Configuration ===
    max_query_size: int = Field(default=100, env="MAX_QUERY_SIZE")
    default_query_size: int = Field(default=20, env="DEFAULT_QUERY_SIZE")
    query_timeout_seconds: int = Field(default=30, env="QUERY_TIMEOUT_SECONDS")
    
    # === Development Configuration ===
    debug_mode: bool = Field(default=False, env="DEBUG_MODE")
    enable_api_docs: bool = Field(default=True, env="ENABLE_API_DOCS")
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }
    
    @field_validator("elasticsearch_backup_hosts", mode="before")
    @classmethod
    def parse_backup_hosts(cls, v):
        """Parse comma-separated backup hosts"""
        if isinstance(v, str):
            return [host.strip() for host in v.split(",") if host.strip()]
        return v or []
    
    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        """Parse comma-separated allowed origins"""
        if isinstance(v, str):
            if v == "*":
                return ["*"]
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v or ["*"]
    
    @field_validator("api_log_level")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level"""
        valid_levels = ["debug", "info", "warning", "error", "critical"]
        if v.lower() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.lower()
    
    @field_validator("nlp_confidence_threshold")
    @classmethod
    def validate_confidence_threshold(cls, v):
        """Validate NLP confidence threshold"""
        if not 0.0 <= v <= 1.0:
            raise ValueError("NLP confidence threshold must be between 0.0 and 1.0")
        return v
    
    @field_validator("max_sessions")
    @classmethod
    def validate_max_sessions(cls, v):
        """Validate max sessions"""
        if v < 1:
            raise ValueError("Max sessions must be at least 1")
        return v
    
    @field_validator("session_timeout_hours")
    @classmethod
    def validate_session_timeout(cls, v):
        """Validate session timeout"""
        if v < 1:
            raise ValueError("Session timeout must be at least 1 hour")
        return v
    
    def get_elasticsearch_hosts(self) -> List[str]:
        """Get all Elasticsearch hosts (primary + backups)"""
        hosts = [self.elasticsearch_host]
        hosts.extend(self.elasticsearch_backup_hosts)
        return hosts
    
    def get_elasticsearch_auth(self) -> Optional[tuple]:
        """Get Elasticsearch authentication tuple"""
        if self.elasticsearch_username and self.elasticsearch_password:
            return (self.elasticsearch_username, self.elasticsearch_password)
        return None
    
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return not self.debug_mode and not self.api_reload
    
    def get_log_config(self) -> dict:
        """Get logging configuration"""
        config = {
            "level": self.log_level.upper(),
            "format": self.log_format
        }
        
        if self.enable_file_logging and self.log_file:
            # Create logs directory if it doesn't exist
            log_path = Path(self.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            config["file"] = str(log_path)
        
        return config


class DevelopmentSettings(Settings):
    """Development-specific settings with sensible defaults"""
    debug_mode: bool = True
    api_reload: bool = True
    api_log_level: str = "debug"
    force_mock_data: bool = True
    enable_api_docs: bool = True
    log_level: str = "DEBUG"


class ProductionSettings(Settings):
    """Production-specific settings with security defaults"""
    debug_mode: bool = False
    api_reload: bool = False
    api_log_level: str = "info"
    force_mock_data: bool = False
    enable_api_docs: bool = False
    log_level: str = "INFO"
    enable_file_logging: bool = True
    allowed_origins: List[str] = []  # Must be explicitly configured


class TestingSettings(Settings):
    """Testing-specific settings"""
    force_mock_data: bool = True
    max_sessions: int = 10
    session_timeout_hours: int = 1
    elasticsearch_timeout: int = 5
    enable_api_docs: bool = False
    log_level: str = "WARNING"


def get_settings(environment: Optional[str] = None) -> Settings:
    """
    Get settings based on environment.
    
    Args:
        environment: Environment name (development, production, testing)
                    If None, determined from ENVIRONMENT env var
    
    Returns:
        Settings instance for the specified environment
    """
    if environment is None:
        environment = os.getenv("ENVIRONMENT", "development").lower()
    
    if environment == "production":
        return ProductionSettings()
    elif environment == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings()


def validate_configuration(settings: Settings) -> List[str]:
    """
    Validate configuration and return list of warnings/issues.
    
    Args:
        settings: Settings instance to validate
    
    Returns:
        List of validation warnings
    """
    warnings = []
    
    # Check for insecure production settings
    if settings.is_production():
        if "*" in settings.allowed_origins:
            warnings.append("CORS is configured to allow all origins in production")
        
        if not settings.elasticsearch_username or not settings.elasticsearch_password:
            warnings.append("Elasticsearch authentication not configured for production")
        
        if not settings.enable_file_logging:
            warnings.append("File logging disabled in production")
        
        if settings.elasticsearch_verify_certs is False:
            warnings.append("Elasticsearch certificate verification disabled in production")
    
    # Check for development conveniences in production
    if settings.is_production() and settings.force_mock_data:
        warnings.append("Mock data forced in production environment")
    
    # Check file paths
    if settings.enable_file_logging and settings.log_file:
        log_dir = Path(settings.log_file).parent
        if not log_dir.exists() and not log_dir.parent.exists():
            warnings.append(f"Log directory parent does not exist: {log_dir.parent}")
    
    # Check model paths
    model_path = Path(settings.nlp_model_path)
    if not model_path.exists() and settings.nlp_model_type != "mock":
        warnings.append(f"NLP model path does not exist: {model_path}")
    
    return warnings


# Global settings instance
settings = get_settings()

# Validate configuration on import
config_warnings = validate_configuration(settings)
if config_warnings:
    print("⚠️  Configuration warnings:")
    for warning in config_warnings:
        print(f"   - {warning}")


def print_config_summary():
    """Print a summary of the current configuration"""
    print("\n📋 SIEM AI Agent Configuration Summary:")
    print(f"   Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"   API: {settings.api_host}:{settings.api_port}")
    print(f"   Debug Mode: {settings.debug_mode}")
    print(f"   Mock Data: {settings.force_mock_data}")
    print(f"   Elasticsearch: {settings.elasticsearch_host}")
    print(f"   Max Sessions: {settings.max_sessions}")
    print(f"   Log Level: {settings.log_level}")
    if config_warnings:
        print(f"   Warnings: {len(config_warnings)} configuration issues detected")
    print()


if __name__ == "__main__":
    # Print configuration when run directly
    print_config_summary()
    
    # Example of how to access settings
    print("Example settings access:")
    print(f"Elasticsearch hosts: {settings.get_elasticsearch_hosts()}")
    print(f"Is production: {settings.is_production()}")
    print(f"Log config: {settings.get_log_config()}")