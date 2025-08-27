"""Configuration settings for the HKEX Settlement Parser."""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Redis Configuration
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "15002"))
    redis_db: int = int(os.getenv("REDIS_DB", "0"))
    redis_password: Optional[str] = os.getenv("REDIS_PASSWORD")
    
    # InfluxDB Configuration
    influxdb_url: str = os.getenv("INFLUXDB_URL", "http://localhost:15003")
    influxdb_token: str = os.getenv("INFLUXDB_TOKEN", "admin-token")
    influxdb_org: str = os.getenv("INFLUXDB_ORG", "hkex")
    influxdb_bucket: str = os.getenv("INFLUXDB_BUCKET", "settlement_data")
    
    # Cassandra Configuration
    cassandra_host: str = os.getenv("CASSANDRA_HOST", "localhost")
    cassandra_port: int = int(os.getenv("CASSANDRA_PORT", "15004"))
    cassandra_keyspace: str = os.getenv("CASSANDRA_KEYSPACE", "hkex_settlement")
    
    # Application Configuration
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    data_dir: str = os.getenv("DATA_DIR", "/app/data")
    hkex_base_url: str = "https://hkex.com/hk/eng/stat/dmstat/datadownload"
    
    class Config:
        env_file = ".env"


settings = Settings()
