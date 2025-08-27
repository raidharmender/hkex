"""Command-line interface for HKEX Settlement Parser."""

import argparse
import logging
import sys
from datetime import date, datetime
from typing import List
from app.services.settlement_parser import settlement_parser
from app.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def download_command(args):
    """Handle download command."""
    try:
        trading_date = date.fromisoformat(args.date)
        logger.info(f"Downloading settlement data for {trading_date}")
        
        result = settlement_parser.download_and_parse(trading_date)
        
        if result["status"] == "success":
            print(f"✅ Successfully downloaded {result['records_count']} records")
            print(f"📅 Trading Date: {trading_date}")
            print(f"⏰ Download Time: {result['download_timestamp']}")
        else:
            print(f"❌ Download failed: {result['message']}")
            sys.exit(1)
            
    except ValueError:
        print(f"❌ Invalid date format: {args.date}. Use YYYY-MM-DD format.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def search_command(args):
    """Handle search command."""
    try:
        if args.date:
            trading_date = date.fromisoformat(args.date)
            records = settlement_parser.search_symbol(args.symbol, trading_date)
        else:
            # Search in most recent data
            trading_dates = settlement_parser.get_trading_dates()
            if not trading_dates:
                print("❌ No trading dates available")
                sys.exit(1)
            
            latest_date = date.fromisoformat(trading_dates[0]["trading_date"])
            records = settlement_parser.search_symbol(args.symbol, latest_date)
            print(f"🔍 Searching in latest available date: {latest_date}")
        
        if records:
            print(f"✅ Found {len(records)} records for symbol '{args.symbol}'")
            print("\n📊 Settlement Records:")
            print("-" * 80)
            print(f"{'Series':<15} {'Expiry':<12} {'Strike':<8} {'Call/Put':<8} {'Settlement':<12} {'Volume':<8} {'OI':<8}")
            print("-" * 80)
            
            for record in records:
                print(f"{record['series']:<15} {record['expiry']:<12} {record['strike']:<8.2f} "
                      f"{record['call_put']:<8} {record['settlement_price']:<12.4f} "
                      f"{record['volume']:<8} {record['open_interest']:<8}")
        else:
            print(f"❌ No records found for symbol '{args.symbol}'")
            
    except ValueError:
        print(f"❌ Invalid date format: {args.date}. Use YYYY-MM-DD format.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def list_dates_command(args):
    """Handle list-dates command."""
    try:
        dates = settlement_parser.get_trading_dates()
        
        if dates:
            print("📅 Available Trading Dates:")
            print("-" * 60)
            print(f"{'Date':<12} {'Records':<10} {'Status':<12} {'Download Time'}")
            print("-" * 60)
            
            for date_info in dates:
                download_time = date_info.get('download_timestamp', 'N/A')
                if isinstance(download_time, datetime):
                    download_time = download_time.strftime('%Y-%m-%d %H:%M')
                
                print(f"{date_info['trading_date']:<12} {date_info['total_records']:<10} "
                      f"{date_info['status']:<12} {download_time}")
        else:
            print("❌ No trading dates available")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def symbols_command(args):
    """Handle symbols command."""
    try:
        trading_date = date.fromisoformat(args.date)
        records = settlement_parser.search_symbol("", trading_date)  # Get all records
        
        if records:
            symbols = list(set(record["series"] for record in records))
            symbols.sort()
            
            print(f"📊 Symbols available for {trading_date}:")
            print("-" * 40)
            for i, symbol in enumerate(symbols, 1):
                print(f"{i:2d}. {symbol}")
            print(f"\nTotal: {len(symbols)} symbols")
        else:
            print(f"❌ No data available for {trading_date}")
            
    except ValueError:
        print(f"❌ Invalid date format: {args.date}. Use YYYY-MM-DD format.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def health_command(args):
    """Handle health command."""
    try:
        from app.database.redis_client import redis_client
        from app.database.influxdb_client import influxdb_client
        from app.database.cassandra_client import cassandra_client
        
        print("🏥 Health Check:")
        print("-" * 30)
        
        redis_status = "✅ Connected" if redis_client.is_connected() else "❌ Disconnected"
        influxdb_status = "✅ Connected" if influxdb_client.is_connected() else "❌ Disconnected"
        cassandra_status = "✅ Connected" if cassandra_client.is_connected() else "❌ Disconnected"
        
        print(f"Redis:     {redis_status}")
        print(f"InfluxDB:  {influxdb_status}")
        print(f"Cassandra: {cassandra_status}")
        
        all_healthy = (
            redis_client.is_connected() and
            influxdb_client.is_connected() and
            cassandra_client.is_connected()
        )
        
        if all_healthy:
            print("\n✅ All services are healthy!")
        else:
            print("\n❌ Some services are not healthy!")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error during health check: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="HKEX Settlement Price Parser CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s download 2023-08-22
  %(prog)s search HTI --date 2023-08-22
  %(prog)s list-dates
  %(prog)s symbols 2023-08-22
  %(prog)s health
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Download command
    download_parser = subparsers.add_parser('download', help='Download settlement data')
    download_parser.add_argument('date', help='Trading date (YYYY-MM-DD)')
    download_parser.set_defaults(func=download_command)
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search for a symbol')
    search_parser.add_argument('symbol', help='Symbol to search for')
    search_parser.add_argument('--date', help='Trading date (YYYY-MM-DD). If not provided, uses latest available date')
    search_parser.set_defaults(func=search_command)
    
    # List dates command
    list_dates_parser = subparsers.add_parser('list-dates', help='List available trading dates')
    list_dates_parser.set_defaults(func=list_dates_command)
    
    # Symbols command
    symbols_parser = subparsers.add_parser('symbols', help='List symbols for a date')
    symbols_parser.add_argument('date', help='Trading date (YYYY-MM-DD)')
    symbols_parser.set_defaults(func=symbols_command)
    
    # Health command
    health_parser = subparsers.add_parser('health', help='Check system health')
    health_parser.set_defaults(func=health_command)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == "__main__":
    main()
