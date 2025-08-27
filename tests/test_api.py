"""API tests for FastAPI endpoints."""

import pytest
from datetime import date
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from app.main import app

client = TestClient(app)


class TestAPIEndpoints:
    """Test cases for API endpoints."""
    
    def test_root_endpoint(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "HKEX Settlement Price Parser API"
        assert data["version"] == "0.1.0"
    
    @patch('app.main.redis_client')
    @patch('app.main.influxdb_client')
    @patch('app.main.cassandra_client')
    def test_health_check_success(self, mock_cassandra, mock_influxdb, mock_redis):
        """Test health check endpoint with all services healthy."""
        mock_redis.is_connected.return_value = True
        mock_influxdb.is_connected.return_value = True
        mock_cassandra.is_connected.return_value = True
        
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["redis"] == "connected"
        assert data["influxdb"] == "connected"
        assert data["cassandra"] == "connected"
    
    @patch('app.main.redis_client')
    @patch('app.main.influxdb_client')
    @patch('app.main.cassandra_client')
    def test_health_check_failure(self, mock_cassandra, mock_influxdb, mock_redis):
        """Test health check endpoint with service failures."""
        mock_redis.is_connected.return_value = False
        mock_influxdb.is_connected.return_value = True
        mock_cassandra.is_connected.return_value = True
        
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["redis"] == "disconnected"
        assert data["influxdb"] == "connected"
        assert data["cassandra"] == "connected"
    
    @patch('app.main.settlement_parser')
    def test_download_endpoint_success(self, mock_parser):
        """Test download endpoint success."""
        mock_parser.download_and_parse.return_value = {
            "status": "success",
            "message": "Successfully processed 100 records",
            "records_count": 100,
            "download_timestamp": "2023-08-22T10:00:00"
        }
        
        response = client.get("/download/2023-08-22")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["records_count"] == 100
        assert "Successfully processed" in data["message"]
    
    @patch('app.main.settlement_parser')
    def test_download_endpoint_failure(self, mock_parser):
        """Test download endpoint failure."""
        mock_parser.download_and_parse.return_value = {
            "status": "error",
            "message": "Failed to download file",
            "records_count": 0,
            "download_timestamp": "2023-08-22T10:00:00"
        }
        
        response = client.get("/download/2023-08-22")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert "Failed to download" in data["message"]
    
    @patch('app.main.cassandra_client')
    def test_get_settlement_data_success(self, mock_cassandra):
        """Test get settlement data endpoint success."""
        mock_records = [
            {
                "series": "HTI2308",
                "expiry": "2023-08-25",
                "strike": 18000.0,
                "call_put": "Call",
                "settlement_price": 0.1234,
                "volume": 100,
                "open_interest": 50,
                "created_at": "2023-08-22T10:00:00"
            }
        ]
        mock_cassandra.get_settlement_records.return_value = mock_records
        
        response = client.get("/data/2023-08-22")
        assert response.status_code == 200
        data = response.json()
        assert data["trading_date"] == "2023-08-22"
        assert data["total_records"] == 1
        assert len(data["records"]) == 1
        assert data["records"][0]["series"] == "HTI2308"
    
    @patch('app.main.cassandra_client')
    def test_get_settlement_data_no_data(self, mock_cassandra):
        """Test get settlement data endpoint with no data."""
        mock_cassandra.get_settlement_records.return_value = []
        
        response = client.get("/data/2023-08-22")
        assert response.status_code == 200
        data = response.json()
        assert data["total_records"] == 0
        assert len(data["records"]) == 0
    
    @patch('app.main.settlement_parser')
    def test_search_symbol_success(self, mock_parser):
        """Test search symbol endpoint success."""
        mock_records = [
            {
                "series": "HTI2308",
                "expiry": "2023-08-25",
                "strike": 18000.0,
                "call_put": "Call",
                "settlement_price": 0.1234,
                "volume": 100,
                "open_interest": 50
            }
        ]
        mock_parser.search_symbol.return_value = mock_records
        
        response = client.post("/search", json={
            "symbol": "HTI",
            "start_date": None,
            "end_date": None
        })
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "HTI"
        assert len(data["records"]) == 1
        assert data["records"][0]["series"] == "HTI2308"
    
    @patch('app.main.settlement_parser')
    def test_search_symbol_by_date_success(self, mock_parser):
        """Test search symbol by date endpoint success."""
        mock_records = [
            {
                "series": "HTI2308",
                "expiry": "2023-08-25",
                "strike": 18000.0,
                "call_put": "Call",
                "settlement_price": 0.1234,
                "volume": 100,
                "open_interest": 50
            }
        ]
        mock_parser.search_symbol.return_value = mock_records
        
        response = client.get("/search/HTI/2023-08-22")
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "HTI"
        assert data["trading_date"] == "2023-08-22"
        assert len(data["records"]) == 1
    
    @patch('app.main.settlement_parser')
    def test_get_trading_dates_success(self, mock_parser):
        """Test get trading dates endpoint success."""
        mock_dates = [
            {
                "trading_date": "2023-08-22",
                "total_records": 100,
                "download_timestamp": "2023-08-22T10:00:00",
                "status": "completed"
            }
        ]
        mock_parser.get_trading_dates.return_value = mock_dates
        
        response = client.get("/trading-dates")
        assert response.status_code == 200
        data = response.json()
        assert len(data["trading_dates"]) == 1
        assert data["trading_dates"][0]["trading_date"] == "2023-08-22"
    
    @patch('app.main.cassandra_client')
    def test_get_symbols_for_date_success(self, mock_cassandra):
        """Test get symbols for date endpoint success."""
        mock_records = [
            {"series": "HTI2308"},
            {"series": "HSI2308"},
            {"series": "HTI2308"}  # Duplicate
        ]
        mock_cassandra.get_settlement_records.return_value = mock_records
        
        response = client.get("/symbols/2023-08-22")
        assert response.status_code == 200
        data = response.json()
        assert data["trading_date"] == "2023-08-22"
        assert len(data["symbols"]) == 2  # Duplicates removed
        assert "HTI2308" in data["symbols"]
        assert "HSI2308" in data["symbols"]
    
    def test_invalid_date_format(self):
        """Test invalid date format handling."""
        response = client.get("/download/invalid-date")
        assert response.status_code == 422  # Validation error
    
    def test_invalid_json_payload(self):
        """Test invalid JSON payload handling."""
        response = client.post("/search", json={"invalid": "payload"})
        assert response.status_code == 422  # Validation error
