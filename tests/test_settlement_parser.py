"""Unit tests for settlement parser service."""

import pytest
from datetime import date
from unittest.mock import Mock, patch, mock_open
from app.services.settlement_parser import SettlementParser


class TestSettlementParser:
    """Test cases for SettlementParser class."""
    
    @pytest.fixture
    def parser(self):
        """Create a parser instance for testing."""
        return SettlementParser()
    
    @pytest.fixture
    def sample_data(self):
        """Sample settlement data for testing."""
        return """Header Line
Series Expiry Strike Call/Put Settlement Volume Open Interest
HTI2308 2023-08-25 18000 Call 0.1234 100 50
HTI2308 2023-08-25 18500 Put 0.5678 200 75
HSI2308 2023-08-25 19000 Call 0.9012 150 60"""
    
    def test_generate_filename(self, parser):
        """Test filename generation."""
        test_date = date(2023, 8, 22)
        expected = "sp220823.dat"
        assert parser._generate_filename(test_date) == expected
    
    def test_generate_url(self, parser):
        """Test URL generation."""
        test_date = date(2023, 8, 22)
        expected = "https://hkex.com/hk/eng/stat/dmstat/datadownload/sp220823.dat"
        assert parser._generate_url(test_date) == expected
    
    @patch('app.services.settlement_parser.requests.get')
    def test_download_file_success(self, mock_get, parser):
        """Test successful file download."""
        mock_response = Mock()
        mock_response.text = "test content"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        with patch('builtins.open', mock_open()) as mock_file:
            result = parser._download_file(date(2023, 8, 22))
            
        assert result is not None
        mock_get.assert_called_once()
        mock_file.assert_called()
    
    @patch('app.services.settlement_parser.requests.get')
    def test_download_file_failure(self, mock_get, parser):
        """Test file download failure."""
        mock_get.side_effect = Exception("Network error")
        
        result = parser._download_file(date(2023, 8, 22))
        
        assert result is None
    
    def test_parse_file_success(self, parser, sample_data):
        """Test successful file parsing."""
        with patch('builtins.open', mock_open(read_data=sample_data)):
            records = parser._parse_file("dummy_path")
        
        assert len(records) == 3
        assert records[0]["series"] == "HTI2308"
        assert records[0]["strike"] == 18000.0
        assert records[0]["call_put"] == "Call"
        assert records[0]["settlement_price"] == 0.1234
        assert records[0]["volume"] == 100
        assert records[0]["open_interest"] == 50
    
    def test_parse_file_no_header(self, parser):
        """Test parsing file without header."""
        data_without_header = "Some random data\nMore data"
        
        with patch('builtins.open', mock_open(read_data=data_without_header)):
            records = parser._parse_file("dummy_path")
        
        assert records == []
    
    def test_parse_file_invalid_data(self, parser):
        """Test parsing file with invalid data."""
        invalid_data = """Header Line
Series Expiry Strike Call/Put Settlement Volume Open Interest
HTI2308 2023-08-25 invalid Call 0.1234 100 50"""
        
        with patch('builtins.open', mock_open(read_data=invalid_data)):
            records = parser._parse_file("dummy_path")
        
        assert len(records) == 0
    
    @patch('app.services.settlement_parser.SettlementParser._download_file')
    @patch('app.services.settlement_parser.SettlementParser._parse_file')
    @patch('app.services.settlement_parser.cassandra_client')
    @patch('app.services.settlement_parser.influxdb_client')
    @patch('app.services.settlement_parser.redis_client')
    def test_download_and_parse_success(
        self, mock_redis, mock_influxdb, mock_cassandra, 
        mock_parse, mock_download, parser
    ):
        """Test successful download and parse."""
        mock_download.return_value = "dummy_path"
        mock_parse.return_value = [
            {"series": "HTI2308", "expiry": "2023-08-25", "strike": 18000.0,
             "call_put": "Call", "settlement_price": 0.1234, "volume": 100, "open_interest": 50}
        ]
        mock_cassandra.insert_settlement_records.return_value = True
        mock_influxdb.write_settlement_data.return_value = True
        mock_redis.set_config.return_value = True
        
        result = parser.download_and_parse(date(2023, 8, 22))
        
        assert result["status"] == "success"
        assert result["records_count"] == 1
        assert "Successfully processed" in result["message"]
    
    @patch('app.services.settlement_parser.SettlementParser._download_file')
    def test_download_and_parse_download_failure(self, mock_download, parser):
        """Test download and parse with download failure."""
        mock_download.return_value = None
        
        result = parser.download_and_parse(date(2023, 8, 22))
        
        assert result["status"] == "error"
        assert "Failed to download file" in result["message"]
    
    @patch('app.services.settlement_parser.SettlementParser._download_file')
    @patch('app.services.settlement_parser.SettlementParser._parse_file')
    def test_download_and_parse_no_records(self, mock_parse, mock_download, parser):
        """Test download and parse with no records."""
        mock_download.return_value = "dummy_path"
        mock_parse.return_value = []
        
        result = parser.download_and_parse(date(2023, 8, 22))
        
        assert result["status"] == "error"
        assert "No valid records found" in result["message"]
    
    @patch('app.services.settlement_parser.cassandra_client')
    @patch('app.services.settlement_parser.redis_client')
    def test_search_symbol_success(self, mock_redis, mock_cassandra, parser):
        """Test successful symbol search."""
        mock_records = [
            {"series": "HTI2308", "expiry": "2023-08-25", "strike": 18000.0,
             "call_put": "Call", "settlement_price": 0.1234, "volume": 100, "open_interest": 50}
        ]
        mock_cassandra.get_settlement_records.return_value = mock_records
        mock_redis.get_cache.return_value = None
        mock_redis.set_cache.return_value = True
        
        result = parser.search_symbol("HTI", date(2023, 8, 22))
        
        assert len(result) == 1
        assert result[0]["series"] == "HTI2308"
    
    @patch('app.services.settlement_parser.cassandra_client')
    @patch('app.services.settlement_parser.redis_client')
    def test_search_symbol_from_cache(self, mock_redis, mock_cassandra, parser):
        """Test symbol search using cached data."""
        cached_records = [
            {"series": "HTI2308", "expiry": "2023-08-25", "strike": 18000.0,
             "call_put": "Call", "settlement_price": 0.1234, "volume": 100, "open_interest": 50}
        ]
        mock_redis.get_cache.return_value = cached_records
        
        result = parser.search_symbol("HTI", date(2023, 8, 22))
        
        assert len(result) == 1
        assert result[0]["series"] == "HTI2308"
        mock_cassandra.get_settlement_records.assert_not_called()
    
    @patch('app.services.settlement_parser.cassandra_client')
    @patch('app.services.settlement_parser.redis_client')
    def test_get_trading_dates_success(self, mock_redis, mock_cassandra, parser):
        """Test successful trading dates retrieval."""
        mock_dates = [
            {"trading_date": "2023-08-22", "total_records": 100, "status": "completed"},
            {"trading_date": "2023-08-21", "total_records": 95, "status": "completed"}
        ]
        mock_cassandra.get_trading_dates.return_value = mock_dates
        mock_redis.get_cache.return_value = None
        mock_redis.set_cache.return_value = True
        
        result = parser.get_trading_dates()
        
        assert len(result) == 2
        assert result[0]["trading_date"] == "2023-08-22"
        assert result[0]["total_records"] == 100
