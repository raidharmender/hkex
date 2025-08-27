"""Main FastAPI application for HKEX Settlement Parser."""

import logging
from datetime import date, datetime
from typing import List
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from app.models import (
    DownloadRequest,
    DownloadResponse,
    SearchRequest,
    SettlementData,
    SettlementRecord,
    HealthCheck,
)
from app.services.settlement_parser import settlement_parser
from app.database.redis_client import redis_client
from app.database.influxdb_client import influxdb_client
from app.database.cassandra_client import cassandra_client
from app.config import settings

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="HKEX Settlement Price Parser",
    description="API for parsing and managing HKEX settlement price files",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("Starting HKEX Settlement Parser application")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("Shutting down HKEX Settlement Parser application")
    influxdb_client.close()
    cassandra_client.close()


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": "HKEX Settlement Price Parser API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthCheck, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return HealthCheck(
        status="healthy",
        redis="connected" if redis_client.is_connected() else "disconnected",
        influxdb="connected" if influxdb_client.is_connected() else "disconnected",
        cassandra="connected" if cassandra_client.is_connected() else "disconnected",
        timestamp=datetime.now(),
    )


@app.post("/download", response_model=DownloadResponse, tags=["Download"])
async def download_settlement_data(
    request: DownloadRequest, background_tasks: BackgroundTasks
):
    """Download and parse settlement data for a specific date."""
    try:
        # Add to background tasks for async processing
        background_tasks.add_task(
            settlement_parser.download_and_parse, request.trading_date
        )
        
        return DownloadResponse(
            trading_date=request.trading_date,
            status="processing",
            message="Download started in background",
            records_count=0,
            download_timestamp=datetime.now(),
        )
    except Exception as e:
        logger.error(f"Error starting download: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download/{trading_date}", response_model=DownloadResponse, tags=["Download"])
async def download_settlement_data_sync(trading_date: date):
    """Download and parse settlement data synchronously."""
    try:
        result = settlement_parser.download_and_parse(trading_date)
        return DownloadResponse(
            trading_date=trading_date,
            status=result["status"],
            message=result["message"],
            records_count=result["records_count"],
            download_timestamp=result["download_timestamp"],
        )
    except Exception as e:
        logger.error(f"Error downloading data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/data/{trading_date}", response_model=SettlementData, tags=["Data"])
async def get_settlement_data(trading_date: date):
    """Get settlement data for a specific date."""
    try:
        records = cassandra_client.get_settlement_records(trading_date.isoformat())
        
        settlement_records = []
        for record in records:
            settlement_records.append(
                SettlementRecord(
                    series=record["series"],
                    expiry=record["expiry"],
                    strike=record["strike"],
                    call_put=record["call_put"],
                    settlement_price=record["settlement_price"],
                    volume=record["volume"],
                    open_interest=record["open_interest"],
                    trading_date=trading_date,
                )
            )
        
        return SettlementData(
            trading_date=trading_date,
            total_records=len(settlement_records),
            records=settlement_records,
            download_timestamp=datetime.now(),
        )
    except Exception as e:
        logger.error(f"Error getting settlement data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search", tags=["Search"])
async def search_symbol(request: SearchRequest):
    """Search for a specific symbol in settlement data."""
    try:
        if request.start_date and request.end_date:
            # Search across date range
            results = []
            current_date = request.start_date
            while current_date <= request.end_date:
                records = settlement_parser.search_symbol(request.symbol, current_date)
                if records:
                    results.extend(records)
                current_date = current_date.replace(day=current_date.day + 1)
            return {"symbol": request.symbol, "records": results}
        else:
            # Search in most recent data
            trading_dates = settlement_parser.get_trading_dates()
            if not trading_dates:
                return {"symbol": request.symbol, "records": []}
            
            latest_date = date.fromisoformat(trading_dates[0]["trading_date"])
            records = settlement_parser.search_symbol(request.symbol, latest_date)
            return {"symbol": request.symbol, "records": records}
    except Exception as e:
        logger.error(f"Error searching symbol: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search/{symbol}/{trading_date}", tags=["Search"])
async def search_symbol_by_date(symbol: str, trading_date: date):
    """Search for a specific symbol on a specific date."""
    try:
        records = settlement_parser.search_symbol(symbol, trading_date)
        return {"symbol": symbol, "trading_date": trading_date, "records": records}
    except Exception as e:
        logger.error(f"Error searching symbol by date: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/trading-dates", tags=["Data"])
async def get_trading_dates():
    """Get list of available trading dates."""
    try:
        dates = settlement_parser.get_trading_dates()
        return {"trading_dates": dates}
    except Exception as e:
        logger.error(f"Error getting trading dates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/symbols/{trading_date}", tags=["Data"])
async def get_symbols_for_date(trading_date: date):
    """Get list of symbols available for a specific date."""
    try:
        records = cassandra_client.get_settlement_records(trading_date.isoformat())
        symbols = list(set(record["series"] for record in records))
        return {"trading_date": trading_date, "symbols": symbols}
    except Exception as e:
        logger.error(f"Error getting symbols: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
