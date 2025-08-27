"""Data models for the HKEX Settlement Parser."""

from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class SettlementRecord(BaseModel):
    """Model for a single settlement record."""
    
    series: str = Field(..., description="Contract series code")
    expiry: str = Field(..., description="Expiry date")
    strike: float = Field(..., description="Strike price")
    call_put: str = Field(..., description="Call or Put option")
    settlement_price: float = Field(..., description="Settlement price")
    volume: int = Field(..., description="Trading volume")
    open_interest: int = Field(..., description="Open interest")
    trading_date: date = Field(..., description="Trading date")


class SettlementData(BaseModel):
    """Model for settlement data response."""
    
    trading_date: date = Field(..., description="Trading date")
    total_records: int = Field(..., description="Total number of records")
    records: List[SettlementRecord] = Field(..., description="List of settlement records")
    download_timestamp: datetime = Field(..., description="When the data was downloaded")


class DownloadRequest(BaseModel):
    """Model for download request."""
    
    trading_date: date = Field(..., description="Trading date to download")
    symbols: Optional[List[str]] = Field(None, description="Specific symbols to filter")


class DownloadResponse(BaseModel):
    """Model for download response."""
    
    trading_date: date = Field(..., description="Trading date")
    status: str = Field(..., description="Download status")
    message: str = Field(..., description="Status message")
    records_count: int = Field(..., description="Number of records downloaded")
    download_timestamp: datetime = Field(..., description="Download timestamp")


class SearchRequest(BaseModel):
    """Model for search request."""
    
    symbol: str = Field(..., description="Symbol to search for")
    start_date: Optional[date] = Field(None, description="Start date for search")
    end_date: Optional[date] = Field(None, description="End date for search")


class HealthCheck(BaseModel):
    """Model for health check response."""
    
    status: str = Field(..., description="Service status")
    redis: str = Field(..., description="Redis connection status")
    influxdb: str = Field(..., description="InfluxDB connection status")
    cassandra: str = Field(..., description="Cassandra connection status")
    timestamp: datetime = Field(..., description="Health check timestamp")
