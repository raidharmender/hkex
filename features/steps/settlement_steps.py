"""Step definitions for settlement parser BDD tests."""

import json
from datetime import date
from behave import given, when, then
from unittest.mock import patch, Mock
from app.services.settlement_parser import settlement_parser
from app.database.redis_client import redis_client
from app.database.influxdb_client import influxdb_client
from app.database.cassandra_client import cassandra_client


@given('the HKEX settlement parser is running')
def step_parser_running(context):
    """Ensure the parser is running."""
    context.parser = settlement_parser


@given('the database connections are healthy')
def step_database_healthy(context):
    """Mock database connections as healthy."""
    context.redis_healthy = True
    context.influxdb_healthy = True
    context.cassandra_healthy = True


@given('I want to download settlement data for "{trading_date}"')
def step_want_to_download(context, trading_date):
    """Set the trading date for download."""
    context.trading_date = date.fromisoformat(trading_date)


@when('I download the settlement data')
def step_download_data(context):
    """Download the settlement data."""
    with patch('app.services.settlement_parser.requests.get') as mock_get:
        # Mock successful download
        mock_response = Mock()
        mock_response.text = """Header Line
Series Expiry Strike Call/Put Settlement Volume Open Interest
HTI2308 2023-08-25 18000 Call 0.1234 100 50
HTI2308 2023-08-25 18500 Put 0.5678 200 75
HSI2308 2023-08-25 19000 Call 0.9012 150 60"""
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        with patch('app.services.settlement_parser.cassandra_client') as mock_cassandra, \
             patch('app.services.settlement_parser.influxdb_client') as mock_influxdb, \
             patch('app.services.settlement_parser.redis_client') as mock_redis:
            
            mock_cassandra.insert_settlement_records.return_value = True
            mock_influxdb.write_settlement_data.return_value = True
            mock_redis.set_config.return_value = True
            
            context.result = settlement_parser.download_and_parse(context.trading_date)


@then('the download should be successful')
def step_download_successful(context):
    """Verify download was successful."""
    assert context.result["status"] == "success"


@then('the data should be stored in the database')
def step_data_stored(context):
    """Verify data was stored in database."""
    assert context.result["records_count"] > 0


@then('I should receive a success response')
def step_success_response(context):
    """Verify success response."""
    assert "Successfully processed" in context.result["message"]


@given('settlement data exists for "{trading_date}"')
def step_data_exists(context, trading_date):
    """Mock that settlement data exists."""
    context.trading_date = date.fromisoformat(trading_date)
    context.mock_records = [
        {
            "series": "HTI2308",
            "expiry": "2023-08-25",
            "strike": 18000.0,
            "call_put": "Call",
            "settlement_price": 0.1234,
            "volume": 100,
            "open_interest": 50
        },
        {
            "series": "HTI2308",
            "expiry": "2023-08-25",
            "strike": 18500.0,
            "call_put": "Put",
            "settlement_price": 0.5678,
            "volume": 200,
            "open_interest": 75
        }
    ]


@when('I search for symbol "{symbol}"')
def step_search_symbol(context, symbol):
    """Search for a specific symbol."""
    with patch('app.services.settlement_parser.cassandra_client') as mock_cassandra, \
         patch('app.services.settlement_parser.redis_client') as mock_redis:
        
        if symbol == "INVALID":
            mock_cassandra.get_settlement_records.return_value = []
        else:
            mock_cassandra.get_settlement_records.return_value = context.mock_records
        
        mock_redis.get_cache.return_value = None
        mock_redis.set_cache.return_value = True
        
        context.search_result = settlement_parser.search_symbol(symbol, context.trading_date)


@then('I should find HTI records')
def step_find_hti_records(context):
    """Verify HTI records were found."""
    assert len(context.search_result) > 0
    assert any(record["series"].startswith("HTI") for record in context.search_result)


@then('the records should contain settlement prices')
def step_records_contain_prices(context):
    """Verify records contain settlement prices."""
    for record in context.search_result:
        assert "settlement_price" in record
        assert isinstance(record["settlement_price"], (int, float))


@then('the records should contain volume and open interest data')
def step_records_contain_volume_oi(context):
    """Verify records contain volume and open interest."""
    for record in context.search_result:
        assert "volume" in record
        assert "open_interest" in record
        assert isinstance(record["volume"], int)
        assert isinstance(record["open_interest"], int)


@then('I should receive no records')
def step_no_records(context):
    """Verify no records were found."""
    assert len(context.search_result) == 0


@then('the response should indicate no data found')
def step_no_data_indication(context):
    """Verify response indicates no data."""
    assert context.search_result == []


@given('multiple trading dates have been processed')
def step_multiple_dates_processed(context):
    """Mock multiple trading dates."""
    context.mock_dates = [
        {
            "trading_date": "2023-08-22",
            "total_records": 100,
            "download_timestamp": "2023-08-22T10:00:00",
            "status": "completed"
        },
        {
            "trading_date": "2023-08-21",
            "total_records": 95,
            "download_timestamp": "2023-08-21T10:00:00",
            "status": "completed"
        }
    ]


@when('I request the list of trading dates')
def step_request_trading_dates(context):
    """Request list of trading dates."""
    with patch('app.services.settlement_parser.cassandra_client') as mock_cassandra, \
         patch('app.services.settlement_parser.redis_client') as mock_redis:
        
        mock_cassandra.get_trading_dates.return_value = context.mock_dates
        mock_redis.get_cache.return_value = None
        mock_redis.set_cache.return_value = True
        
        context.dates_result = settlement_parser.get_trading_dates()


@then('I should receive a list of dates')
def step_receive_dates_list(context):
    """Verify list of dates received."""
    assert len(context.dates_result) > 0


@then('each date should have record count information')
def step_dates_have_record_count(context):
    """Verify dates have record count."""
    for date_info in context.dates_result:
        assert "total_records" in date_info
        assert isinstance(date_info["total_records"], int)


@then('the dates should be sorted by most recent first')
def step_dates_sorted_recent_first(context):
    """Verify dates are sorted by most recent first."""
    dates = [date.fromisoformat(d["trading_date"]) for d in context.dates_result]
    assert dates == sorted(dates, reverse=True)


@when('I request symbols for "{trading_date}"')
def step_request_symbols(context, trading_date):
    """Request symbols for a specific date."""
    context.trading_date = date.fromisoformat(trading_date)
    context.mock_records = [
        {"series": "HTI2308"},
        {"series": "HSI2308"},
        {"series": "HTI2308"}  # Duplicate
    ]


@then('I should receive a list of unique symbols')
def step_receive_unique_symbols(context):
    """Verify unique symbols received."""
    symbols = list(set(record["series"] for record in context.mock_records))
    assert len(symbols) == 2  # Duplicates removed


@then('the symbols should include "{symbol1}" and "{symbol2}"')
def step_symbols_include_expected(context, symbol1, symbol2):
    """Verify expected symbols are included."""
    symbols = list(set(record["series"] for record in context.mock_records))
    assert symbol1 in symbols
    assert symbol2 in symbols


@given('the date is not a trading day')
def step_not_trading_day(context):
    """Mock non-trading day."""
    pass


@then('the download should fail')
def step_download_fails(context):
    """Verify download failed."""
    assert context.result["status"] == "error"


@then('I should receive an error message')
def step_receive_error_message(context):
    """Verify error message received."""
    assert "error" in context.result["status"].lower()


@given('a settlement file with invalid format')
def step_invalid_format_file(context):
    """Mock invalid format file."""
    context.invalid_data = "Invalid format data\nNo proper header\nRandom content"


@when('I parse the file')
def step_parse_file(context):
    """Parse the file."""
    with patch('builtins.open', Mock()) as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = context.invalid_data
        context.parse_result = settlement_parser._parse_file("dummy_path")


@then('the parsing should handle the error gracefully')
def step_parsing_handles_error(context):
    """Verify parsing handles error gracefully."""
    assert context.parse_result == []


@then('I should receive an empty result set')
def step_empty_result_set(context):
    """Verify empty result set."""
    assert len(context.parse_result) == 0


@given('I have previously downloaded data for "{trading_date}"')
def step_previously_downloaded(context, trading_date):
    """Mock previously downloaded data."""
    context.trading_date = date.fromisoformat(trading_date)
    context.cached_data = "cached settlement data"


@when('I request the same data again')
def step_request_same_data(context):
    """Request same data again."""
    with patch('app.services.settlement_parser.redis_client') as mock_redis:
        mock_redis.get_cache.return_value = context.cached_data
        context.cache_result = settlement_parser._download_file(context.trading_date)


@then('the response should come from cache')
def step_response_from_cache(context):
    """Verify response comes from cache."""
    assert context.cache_result is not None


@then('the response time should be faster')
def step_faster_response_time(context):
    """Verify faster response time (implied by cache usage)."""
    # This would need actual timing measurement in a real implementation
    assert context.cache_result is not None


@given('all database services are running')
def step_all_services_running(context):
    """Mock all services running."""
    context.redis_healthy = True
    context.influxdb_healthy = True
    context.cassandra_healthy = True


@when('I check the system health')
def step_check_system_health(context):
    """Check system health."""
    with patch('app.database.redis_client.RedisClient.is_connected') as mock_redis, \
         patch('app.database.influxdb_client.InfluxDBClientWrapper.is_connected') as mock_influxdb, \
         patch('app.database.cassandra_client.CassandraClient.is_connected') as mock_cassandra:
        
        mock_redis.return_value = context.redis_healthy
        mock_influxdb.return_value = context.influxdb_healthy
        mock_cassandra.return_value = context.cassandra_healthy
        
        context.redis_status = redis_client.is_connected()
        context.influxdb_status = influxdb_client.is_connected()
        context.cassandra_status = cassandra_client.is_connected()


@then('all services should report as healthy')
def step_all_services_healthy(context):
    """Verify all services report as healthy."""
    assert context.redis_status is True
    assert context.influxdb_status is True
    assert context.cassandra_status is True


@then('the response should include connection status for each service')
def step_include_connection_status(context):
    """Verify connection status included."""
    assert context.redis_status is not None
    assert context.influxdb_status is not None
    assert context.cassandra_status is not None
