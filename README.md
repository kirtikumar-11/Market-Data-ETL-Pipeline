# Market Data ETL Pipeline

A Python-based market data ETL pipeline that extracts market data from an API, validates and transforms the data, detects outliers, calculates VWAP, and loads the processed records into PostgreSQL.

## Project Overview

This project demonstrates a complete ETL workflow for market data processing.

The pipeline performs the following operations:

1. Extracts market data from an external API.
2. Validates incoming records using Pydantic.
3. Handles invalid records through dead-letter logging.
4. Calculates Volume Weighted Average Price (VWAP).
5. Detects price outliers using the IQR method.
6. Loads processed records into PostgreSQL.
7. Prevents duplicate records using a unique constraint.
8. Logs pipeline activities in JSON format.
9. Supports continuous batch processing.

## Architecture

```text
Market Data API
       |
       v
Data Extraction
       |
       v
Data Validation
       |
       v
Data Transformation
       |
       +--> VWAP Calculation
       |
       +--> IQR Outlier Detection
       |
       v
PostgreSQL Database
       |
       v
Structured Logs
```

## Technology Stack

- Python
- FastAPI
- Pydantic
- PostgreSQL
- NumPy
- Requests
- Docker
- Docker Compose
- Pytest
- JSON Logging

## Project Structure

```text
market-data-etl/
│
├── api/
│   └── ...
│
├── db/
│   └── ...
│
├── etl/
│   ├── main.py
│   └── tests/
│
├── logs/
│
├── .env.example
├── .gitignore
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Key Features

### Data Extraction

- Fetches market data from an API.
- Uses retry handling for temporary API failures.
- Applies request timeouts.
- Supports repeated batch execution.

### Data Validation

Incoming records are validated using Pydantic.

Validation includes:

- Instrument identifier
- Positive price
- Non-negative volume
- Valid timestamp
- Optional VWAP
- Outlier status

Invalid records are excluded from processing and recorded in the dead-letter log.

### VWAP Calculation

The pipeline calculates Volume Weighted Average Price using the following formula:

\[
VWAP = rac{\sum(price 	imes volume)}{\sum(volume)}
\]

VWAP is calculated separately for each instrument.

### Outlier Detection

Price outliers are detected using the Interquartile Range method.

```text
IQR = Q3 - Q1

Lower Bound = Q1 - 1.5 × IQR
Upper Bound = Q3 + 1.5 × IQR
```

Records outside the calculated bounds are marked as outliers.

### Database Loading

Processed records are stored in PostgreSQL.

The loading process includes:

- Database connection retry handling
- Transaction management
- Duplicate record prevention
- Batch insertion
- Error logging

## Database Schema

The main table is:

```text
marketdata
```

The table stores:

- Instrument ID
- Price
- Volume
- Timestamp
- VWAP
- Outlier flag

## Configuration

Create a local environment file using `.env.example` and configure the required API and PostgreSQL settings.

The application uses environment variables for configuration so that deployment-specific values are not hardcoded in the source code.

## Running the Project

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/<your-repository>.git
cd <your-repository>
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the services

```bash
docker compose up -d
```

### 5. Run the ETL pipeline

```bash
python etl/main.py
```

## Testing

The project includes automated tests covering the main ETL components.

Run the tests using:

```bash
pytest
```

## Logging

The pipeline generates structured JSON logs for:

- API extraction
- Validation failures
- Transformation results
- Database operations
- Outlier detection
- Pipeline errors

## Future Improvements

Possible future enhancements include:

- Adding Apache Kafka for real-time ingestion
- Integrating Apache Spark for distributed processing
- Adding cloud storage support
- Introducing monitoring and alerting
- Adding data quality dashboards
- Supporting multiple market data providers

## Author

**Kirtikumar**


