"""Settlement parser service for HKEX data."""

import logging
import os
from datetime import date, datetime
from typing import Dict, List, Optional
import requests
import pandas as pd
from app.config import settings
from app.database.redis_client import redis_client
from app.database.influxdb_client import influxdb_client
from app.database.cassandra_client import cassandra_client

logger = logging.getLogger(__name__)


class SettlementParser:
    """Parser for HKEX settlement price files."""
    
    def __init__(self) -> None:
        """Initialize the settlement parser."""
        self.base_url = settings.hkex_base_url
        self.data_dir = settings.data_dir
        os.makedirs(self.data_dir, exist_ok=True)
    
    def _generate_filename(self, trading_date: date) -> str:
        """Generate filename for the trading date."""
        return f"sp{trading_date.strftime('%d%m%y')}.dat"
    
    def _generate_url(self, trading_date: date) -> str:
        """Generate URL for the trading date."""
        filename = self._generate_filename(trading_date)
        return f"{self.base_url}/{filename}"
    
    def _download_file(self, trading_date: date) -> Optional[str]:
        """Download settlement file from HKEX."""
        url = self._generate_url(trading_date)
        filename = self._generate_filename(trading_date)
        filepath = os.path.join(self.data_dir, filename)
        
        # Check cache first
        cache_key = f"settlement_file:{trading_date.isoformat()}"
        cached_content = redis_client.get_cache(cache_key)
        if cached_content:
            logger.info(f"Using cached file for {trading_date}")
            with open(filepath, 'w') as f:
                f.write(cached_content)
            return filepath
        
        try:
            logger.info(f"Downloading settlement file from {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Cache the content
            redis_client.set_cache(cache_key, response.text, expire=3600)
            
            # Save to file
            with open(filepath, 'w') as f:
                f.write(response.text)
            
            logger.info(f"Successfully downloaded {filename}")
            return filepath
        except requests.RequestException as e:
            logger.error(f"Failed to download file for {trading_date}: {e}")
            return None
    
    def _parse_file(self, filepath: str) -> List[Dict]:
        """Parse the settlement file and extract records."""
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            
            lines = content.splitlines()
            
            # Find header line
            header_idx = None
            for i, line in enumerate(lines):
                if line.strip().startswith('Series'):
                    header_idx = i
                    break
            
            if header_idx is None:
                logger.error("Could not find header line in file")
                return []
            
            # Extract column names
            columns = lines[header_idx].split()
            
            # Extract data rows
            data_rows = []
            for line in lines[header_idx + 1:]:
                if line.strip():
                    data_rows.append(line.split())
            
            # Create DataFrame
            df = pd.DataFrame(data_rows, columns=columns)
            
            # Convert to records
            records = []
            for _, row in df.iterrows():
                try:
                    record = {
                        "series": row["Series"],
                        "expiry": row["Expiry"],
                        "strike": float(row["Strike"]),
                        "call_put": row["Call/Put"],
                        "settlement_price": float(row["Settlement"]),
                        "volume": int(row["Volume"]),
                        "open_interest": int(row["Open Interest"]),
                    }
                    records.append(record)
                except (ValueError, KeyError) as e:
                    logger.warning(f"Skipping invalid row: {e}")
                    continue
            
            logger.info(f"Parsed {len(records)} records from file")
            return records
        except Exception as e:
            logger.error(f"Failed to parse file {filepath}: {e}")
            return []
    
    def download_and_parse(self, trading_date: date) -> Dict:
        """Download and parse settlement data for a specific date."""
        try:
            # Download file
            filepath = self._download_file(trading_date)
            if not filepath:
                return {
                    "status": "error",
                    "message": f"Failed to download file for {trading_date}",
                    "records_count": 0,
                    "download_timestamp": datetime.now(),
                }
            
            # Parse file
            records = self._parse_file(filepath)
            if not records:
                return {
                    "status": "error",
                    "message": f"No valid records found for {trading_date}",
                    "records_count": 0,
                    "download_timestamp": datetime.now(),
                }
            
            # Store in databases
            trading_date_str = trading_date.isoformat()
            
            # Store in Cassandra
            cassandra_success = cassandra_client.insert_settlement_records(
                trading_date_str, records
            )
            
            # Store in InfluxDB
            influxdb_success = influxdb_client.write_settlement_data(
                trading_date_str, records
            )
            
            # Store metadata in Redis
            metadata = {
                "trading_date": trading_date_str,
                "total_records": len(records),
                "download_timestamp": datetime.now().isoformat(),
                "cassandra_success": cassandra_success,
                "influxdb_success": influxdb_success,
            }
            redis_client.set_config(f"settlement_metadata:{trading_date_str}", metadata)
            
            return {
                "status": "success",
                "message": f"Successfully processed {len(records)} records for {trading_date}",
                "records_count": len(records),
                "download_timestamp": datetime.now(),
            }
        except Exception as e:
            logger.error(f"Error processing settlement data for {trading_date}: {e}")
            return {
                "status": "error",
                "message": f"Error processing data: {str(e)}",
                "records_count": 0,
                "download_timestamp": datetime.now(),
            }
    
    def search_symbol(self, symbol: str, trading_date: date) -> List[Dict]:
        """Search for a specific symbol in settlement data."""
        try:
            # Try to get from cache first
            cache_key = f"symbol_search:{symbol}:{trading_date.isoformat()}"
            cached_result = redis_client.get_cache(cache_key)
            if cached_result:
                return cached_result
            
            # Get from Cassandra
            records = cassandra_client.get_settlement_records(
                trading_date.isoformat(), symbol
            )
            
            # Cache the result
            redis_client.set_cache(cache_key, records, expire=1800)
            
            return records
        except Exception as e:
            logger.error(f"Error searching for symbol {symbol}: {e}")
            return []
    
    def get_trading_dates(self) -> List[Dict]:
        """Get list of available trading dates."""
        try:
            # Try to get from cache first
            cache_key = "trading_dates"
            cached_result = redis_client.get_cache(cache_key)
            if cached_result:
                return cached_result
            
            # Get from Cassandra
            dates = cassandra_client.get_trading_dates()
            
            # Cache the result
            redis_client.set_cache(cache_key, dates, expire=3600)
            
            return dates
        except Exception as e:
            logger.error(f"Error getting trading dates: {e}")
            return []


settlement_parser = SettlementParser()
