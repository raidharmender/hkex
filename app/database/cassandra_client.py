"""Cassandra client for document-based data storage."""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from app.config import settings

logger = logging.getLogger(__name__)


class CassandraClient:
    """Cassandra client for document storage."""
    
    def __init__(self) -> None:
        """Initialize Cassandra client."""
        self.cluster = Cluster(
            [settings.cassandra_host],
            port=settings.cassandra_port,
        )
        self.session = None
        self._setup_keyspace()
    
    def _setup_keyspace(self) -> None:
        """Setup keyspace and tables."""
        try:
            self.session = self.cluster.connect()
            
            # Create keyspace
            keyspace_query = f"""
            CREATE KEYSPACE IF NOT EXISTS {settings.cassandra_keyspace}
            WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 1}}
            """
            self.session.execute(keyspace_query)
            
            # Use keyspace
            self.session.set_keyspace(settings.cassandra_keyspace)
            
            # Create tables
            self._create_tables()
            
            logger.info("Cassandra keyspace and tables setup completed")
        except Exception as e:
            logger.error(f"Failed to setup Cassandra: {e}")
    
    def _create_tables(self) -> None:
        """Create necessary tables."""
        # Settlement records table
        settlement_table = """
        CREATE TABLE IF NOT EXISTS settlement_records (
            trading_date date,
            series text,
            expiry text,
            strike decimal,
            call_put text,
            settlement_price decimal,
            volume int,
            open_interest int,
            created_at timestamp,
            PRIMARY KEY (trading_date, series, expiry, strike, call_put)
        )
        """
        
        # Trading dates table
        trading_dates_table = """
        CREATE TABLE IF NOT EXISTS trading_dates (
            trading_date date PRIMARY KEY,
            total_records int,
            download_timestamp timestamp,
            status text
        )
        """
        
        # Symbol metadata table
        symbol_metadata_table = """
        CREATE TABLE IF NOT EXISTS symbol_metadata (
            symbol text PRIMARY KEY,
            first_trading_date date,
            last_trading_date date,
            total_records int,
            updated_at timestamp
        )
        """
        
        self.session.execute(settlement_table)
        self.session.execute(trading_dates_table)
        self.session.execute(symbol_metadata_table)
    
    def is_connected(self) -> bool:
        """Check if Cassandra is connected."""
        try:
            self.session.execute("SELECT release_version FROM system.local")
            return True
        except Exception:
            return False
    
    def insert_settlement_records(self, trading_date: str, records: List[Dict]) -> bool:
        """Insert settlement records into Cassandra."""
        try:
            insert_query = """
            INSERT INTO settlement_records (
                trading_date, series, expiry, strike, call_put,
                settlement_price, volume, open_interest, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            prepared = self.session.prepare(insert_query)
            
            for record in records:
                self.session.execute(prepared, (
                    datetime.strptime(trading_date, "%Y-%m-%d").date(),
                    record["series"],
                    record["expiry"],
                    float(record["strike"]),
                    record["call_put"],
                    float(record["settlement_price"]),
                    int(record["volume"]),
                    int(record["open_interest"]),
                    datetime.now(),
                ))
            
            # Update trading dates table
            trading_date_query = """
            INSERT INTO trading_dates (trading_date, total_records, download_timestamp, status)
            VALUES (?, ?, ?, ?)
            """
            prepared_trading = self.session.prepare(trading_date_query)
            self.session.execute(prepared_trading, (
                datetime.strptime(trading_date, "%Y-%m-%d").date(),
                len(records),
                datetime.now(),
                "completed"
            ))
            
            logger.info(f"Inserted {len(records)} settlement records to Cassandra")
            return True
        except Exception as e:
            logger.error(f"Failed to insert settlement records: {e}")
            return False
    
    def get_settlement_records(
        self,
        trading_date: str,
        symbol: Optional[str] = None
    ) -> List[Dict]:
        """Get settlement records from Cassandra."""
        try:
            if symbol:
                query = """
                SELECT * FROM settlement_records 
                WHERE trading_date = ? AND series LIKE ?
                """
                prepared = self.session.prepare(query)
                rows = self.session.execute(prepared, (
                    datetime.strptime(trading_date, "%Y-%m-%d").date(),
                    f"{symbol}%"
                ))
            else:
                query = "SELECT * FROM settlement_records WHERE trading_date = ?"
                prepared = self.session.prepare(query)
                rows = self.session.execute(prepared, (
                    datetime.strptime(trading_date, "%Y-%m-%d").date(),
                ))
            
            records = []
            for row in rows:
                records.append({
                    "series": row.series,
                    "expiry": row.expiry,
                    "strike": float(row.strike),
                    "call_put": row.call_put,
                    "settlement_price": float(row.settlement_price),
                    "volume": row.volume,
                    "open_interest": row.open_interest,
                    "created_at": row.created_at,
                })
            
            logger.info(f"Retrieved {len(records)} records from Cassandra")
            return records
        except Exception as e:
            logger.error(f"Failed to get settlement records: {e}")
            return []
    
    def get_trading_dates(self) -> List[Dict]:
        """Get list of trading dates."""
        try:
            query = "SELECT * FROM trading_dates ORDER BY trading_date DESC"
            rows = self.session.execute(query)
            
            dates = []
            for row in rows:
                dates.append({
                    "trading_date": row.trading_date.isoformat(),
                    "total_records": row.total_records,
                    "download_timestamp": row.download_timestamp,
                    "status": row.status,
                })
            
            return dates
        except Exception as e:
            logger.error(f"Failed to get trading dates: {e}")
            return []
    
    def close(self) -> None:
        """Close Cassandra connection."""
        if self.session:
            self.session.shutdown()
        if self.cluster:
            self.cluster.shutdown()


cassandra_client = CassandraClient()
