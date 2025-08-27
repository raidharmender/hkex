# HKEX Settlement Price Parser

A comprehensive Python-based application for downloading, parsing, and managing HKEX (Hong Kong Exchanges and Clearing Limited) settlement price files. The application provides both REST API and command-line interfaces for processing stock option contract data.

## 🏗️ Architecture

The application follows a microservices architecture with the following components:

- **FastAPI Backend**: RESTful API with Swagger documentation
- **Redis**: Configuration storage and caching
- **InfluxDB**: Time-series data storage
- **Cassandra**: Document-based data storage
- **Docker**: Containerized deployment

### Architecture Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │   Command Line  │    │   External      │
│   (Port 15001)  │    │   Interface     │    │   HKEX API      │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────┴─────────────┐
                    │                           │
          ┌─────────▼─────────┐    ┌───────────▼───────────┐
          │      Redis        │    │      InfluxDB         │
          │   (Port 15002)     │    │     (Port 15003)      │
          │   Config/Cache     │    │   Time-series Data    │
          └───────────────────┘    └───────────────────────┘
                    │                           │
                    └───────────┬───────────────┘
                                │
                    ┌───────────▼───────────┐
                    │      Cassandra       │
                    │     (Port 15004)     │
                    │   Document Storage   │
                    └───────────────────────┘
```

## 🚀 Features

- **Multi-day Download Support**: Download settlement data for multiple trading days
- **Symbol Search**: Search for specific symbols (e.g., HTI) across trading dates
- **REST API**: Full RESTful API with Swagger documentation
- **Command Line Interface**: Easy-to-use CLI for data operations
- **Caching**: Redis-based caching for improved performance
- **Data Storage**: Multi-database storage strategy:
  - Redis: Configuration and cache
  - InfluxDB: Time-series data
  - Cassandra: Document-based data
- **Health Monitoring**: System health checks for all services
- **Comprehensive Testing**: TDD and BDD test coverage

## 📋 Prerequisites

- Python 3.11+
- Docker and Docker Compose
- uv (Python package manager)

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd settlement
   ```

2. **Install dependencies using uv**:
   ```bash
   uv pip install -e .
   ```

3. **Start the services using Docker Compose**:
   ```bash
   docker-compose up -d
   ```

## 🏃‍♂️ Quick Start

### Using the Command Line Interface

1. **Download settlement data for August 22, 2023**:
   ```bash
   python -m app.cli download 2023-08-22
   ```

2. **Search for HTI symbol**:
   ```bash
   python -m app.cli search HTI --date 2023-08-22
   ```

3. **List available trading dates**:
   ```bash
   python -m app.cli list-dates
   ```

4. **Check system health**:
   ```bash
   python -m app.cli health
   ```

### Using the REST API

1. **Access Swagger documentation**:
   ```
   http://localhost:15001/docs
   ```

2. **Download settlement data**:
   ```bash
   curl -X GET "http://localhost:15001/download/2023-08-22"
   ```

3. **Search for HTI symbol**:
   ```bash
   curl -X POST "http://localhost:15001/search" \
        -H "Content-Type: application/json" \
        -d '{"symbol": "HTI", "start_date": "2023-08-22", "end_date": "2023-08-22"}'
   ```

4. **Get settlement data**:
   ```bash
   curl -X GET "http://localhost:15001/data/2023-08-22"
   ```

## 🧪 Testing

### Running Unit Tests (TDD)
```bash
pytest tests/
```

### Running BDD Tests
```bash
behave features/
```

### Running All Tests
```bash
pytest tests/ && behave features/
```

## 📊 API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root endpoint with API info |
| GET | `/health` | System health check |
| GET | `/download/{trading_date}` | Download settlement data |
| POST | `/download` | Download data (async) |
| GET | `/data/{trading_date}` | Get settlement data |
| POST | `/search` | Search for symbols |
| GET | `/search/{symbol}/{trading_date}` | Search symbol by date |
| GET | `/trading-dates` | List available trading dates |
| GET | `/symbols/{trading_date}` | Get symbols for date |

### Example API Usage

```python
import requests

# Download data for August 22, 2023
response = requests.get("http://localhost:15001/download/2023-08-22")
print(response.json())

# Search for HTI symbol
search_data = {
    "symbol": "HTI",
    "start_date": "2023-08-22",
    "end_date": "2023-08-22"
}
response = requests.post("http://localhost:15001/search", json=search_data)
print(response.json())
```

## 🔧 Configuration

The application uses environment variables for configuration:

```bash
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=15002
REDIS_DB=0

# InfluxDB Configuration
INFLUXDB_URL=http://localhost:15003
INFLUXDB_TOKEN=admin-token
INFLUXDB_ORG=hkex
INFLUXDB_BUCKET=settlement_data

# Cassandra Configuration
CASSANDRA_HOST=localhost
CASSANDRA_PORT=15004
CASSANDRA_KEYSPACE=hkex_settlement

# Application Configuration
LOG_LEVEL=INFO
DATA_DIR=/app/data
```

## 🐳 Docker Deployment

### Building the Application
```bash
docker build -t hkex-settlement-parser .
```

### Running with Docker Compose
```bash
docker-compose up -d
```

### Service Ports
- **FastAPI App**: 15001
- **Redis**: 15002
- **InfluxDB**: 15003
- **Cassandra**: 15004

## 📈 Data Flow

1. **Download**: Fetch settlement files from HKEX
2. **Parse**: Extract structured data from files
3. **Store**: Save data to multiple databases:
   - Cassandra: Document storage
   - InfluxDB: Time-series data
   - Redis: Cache and metadata
4. **Query**: Retrieve data via API or CLI
5. **Search**: Filter data by symbols and dates

## 🔍 Data Structure

### Settlement Record
```json
{
  "series": "HTI2308",
  "expiry": "2023-08-25",
  "strike": 18000.0,
  "call_put": "Call",
  "settlement_price": 0.1234,
  "volume": 100,
  "open_interest": 50,
  "trading_date": "2023-08-22"
}
```

## 🛡️ Error Handling

The application includes comprehensive error handling:

- **Network Errors**: Retry logic for failed downloads
- **Data Validation**: Input validation and sanitization
- **Database Errors**: Graceful handling of connection issues
- **File Parsing**: Robust parsing with error recovery

## 📝 Logging

The application uses structured logging with different levels:

- **INFO**: General application events
- **WARNING**: Non-critical issues
- **ERROR**: Critical errors requiring attention
- **DEBUG**: Detailed debugging information

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:

- Create an issue in the repository
- Check the documentation at `/docs` endpoint
- Review the test cases for usage examples

## 🔄 Version History

- **v0.1.0**: Initial release with basic functionality
  - FastAPI backend
  - CLI interface
  - Multi-database storage
  - Comprehensive testing
