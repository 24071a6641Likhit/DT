"""Application settings"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application configuration"""
    
    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/energy_monitoring"
    
    # Application
    timezone: str = "Asia/Kolkata"
    log_level: str = "INFO"
    
    # Analysis
    polling_interval_seconds: int = 5
    spike_threshold_percentage: int = 50
    rolling_average_window_minutes: int = 60
    data_retention_days: int = 7
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
