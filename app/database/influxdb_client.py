"""InfluxDB client for time series data storage."""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from app.config import settings

logger = logging.getLogger(__name__)


class InfluxDBClientWrapper:
    """InfluxDB client wrapper for time series data."""
    
    def __init__(self) -> None:
        """Initialize InfluxDB client."""
        self.client = InfluxDBClient(
            url=settings.influxdb_url,
            token=settings.influxdb_token,
            org=settings.influxdb_org,
        )
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.query_api = self.client.query_api()
    
    def is_connected(self) -> bool:
        """Check if InfluxDB is connected."""
        try:
            health = self.client.health()
            return health.status == "pass"
        except Exception:
            return False
    
    def write_settlement_data(self, trading_date: str, records: List[Dict]) -> bool:
        """Write settlement data to InfluxDB."""
        try:
            points = []
            for record in records:
                point = Point("settlement_price") \
                    .tag("series", record["series"]) \
                    .tag("expiry", record["expiry"]) \
                    .tag("call_put", record["call_put"]) \
                    .field("strike", record["strike"]) \
                    .field("settlement_price", record["settlement_price"]) \
                    .field("volume", record["volume"]) \
                    .field("open_interest", record["open_interest"]) \
                    .time(datetime.strptime(trading_date, "%Y-%m-%d"))
                points.append(point)
            
            self.write_api.write(
                bucket=settings.influxdb_bucket,
                org=settings.influxdb_org,
                record=points
            )
            logger.info(f"Written {len(points)} settlement records to InfluxDB")
            return True
        except Exception as e:
            logger.error(f"Failed to write settlement data: {e}")
            return False
    
    def query_settlement_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict]:
        """Query settlement data from InfluxDB."""
        try:
            query = f'''
            from(bucket: "{settings.influxdb_bucket}")
                |> range(start: {start_date or "-30d"}, stop: {end_date or "now()"})
                |> filter(fn: (r) => r["_measurement"] == "settlement_price")
                |> filter(fn: (r) => r["series"] == "{symbol}")
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            '''
            
            result = self.query_api.query(query=query, org=settings.influxdb_org)
            
            records = []
            for table in result:
                for record in table.records:
                    records.append({
                        "time": record.get_time(),
                        "series": record.values.get("series"),
                        "expiry": record.values.get("expiry"),
                        "call_put": record.values.get("call_put"),
                        "strike": record.values.get("strike"),
                        "settlement_price": record.values.get("settlement_price"),
                        "volume": record.values.get("volume"),
                        "open_interest": record.values.get("open_interest"),
                    })
            
            logger.info(f"Retrieved {len(records)} records for symbol {symbol}")
            return records
        except Exception as e:
            logger.error(f"Failed to query settlement data: {e}")
            return []
    
    def close(self) -> None:
        """Close InfluxDB client connection."""
        self.client.close()


influxdb_client = InfluxDBClientWrapper()
