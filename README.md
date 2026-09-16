# Market Data ETL Pipeline

## 1. Project Overview

This project implements a market data ETL pipeline that extracts market data from an API, validates and transforms the records, detects price outliers, and loads the processed data into PostgreSQL.

The pipeline is containerized using Docker Compose.

## 2. Architecture

```text
Market Data API
      |
      v
   Extract
      |
      v
   Validate
      |
      v
 Calculate VWAP
      |
      v
 Detect Outliers
      |
      v
 PostgreSQL
```

## 3. Technologies Used

* Python 3.12
* Requests
* Pydantic
* NumPy
* PostgreSQL
* Psycopg2
* Docker
* Docker Compose
* Pytest
* Python JSON Logger

## 4. ETL Workflow

### Extract

The pipeline retrieves market data from the configured API endpoint.

Features:

* HTTP request timeout
* Retry mechanism
* Exponential backoff
* Graceful shutdown support
* Error logging

### Validate

Each record is validated using a Pydantic model.

Validation includes:

* `instrument_id` must be a string
* `price` must be greater than zero
* `volume` must be greater than or equal to zero
* `timestamp` must be a valid datetime
* Optional VWAP field
* Outlier flag

Timestamps are normalized to UTC.

Invalid records are rejected and written to the dead-letter log.

### Calculate VWAP

The pipeline calculates Volume Weighted Average Price for each instrument.

Formula:

```text
VWAP = Sum(Price × Volume) / Sum(Volume)
```

The calculated VWAP is assigned to each record belonging to the same instrument.

If the total volume is zero, VWAP is stored as `None`.

### Detect Outliers

The pipeline uses the Interquartile Range method.

```text
IQR = Q3 - Q1

Lower Bound = Q1 - 1.5 × IQR

Upper Bound = Q3 + 1.5 × IQR
```

A record is marked as an outlier when its price is outside the calculated bounds for its instrument.

### Load

Validated and transformed records are inserted into PostgreSQL.

The loading process includes:

* Database connection retries
* Batch insertion
* Transaction commit
* Transaction rollback on failure
* Duplicate protection
* Inserted and duplicate record logging

## 5. Database

Database name:

```text
market_data
```

Table name:

```text
marketdata
```

The table stores:

* Instrument ID
* Price
* Volume
* Timestamp
* VWAP
* Outlier flag

The pipeline uses the following duplicate-protection rule:

```sql
ON CONFLICT (instrument_id, timestamp) DO NOTHING
```

## 6. Environment Variables

Create a `.env` file in the project root:

```env
API_URL=your_api_url

DB_HOST=postgres
DB_PORT=5432
DB_NAME=market_data
DB_USER=postgres
DB_PASSWORD=your_password
```

Do not commit the actual `.env` file to Git.

## 7. Running the Project

Build and start the services:

```bash
docker compose up --build
```

Start the ETL service:

```bash
docker compose up etl
```

Run the services in detached mode:

```bash
docker compose up -d
```

Check running containers:

```bash
docker compose ps
```

Stop the services:

```bash
docker compose down
```

## 8. Database Verification

List databases:

```bash
docker compose exec postgres psql -U postgres -c "\l"
```

List tables:

```bash
docker compose exec postgres psql -U postgres -d market_data -c "\dt"
```

Inspect the table:

```bash
docker compose exec postgres psql -U postgres -d market_data -c "\d marketdata"
```

View loaded records:

```bash
docker compose exec postgres psql -U postgres -d market_data -c "SELECT * FROM marketdata LIMIT 10;"
```

Count records:

```bash
docker compose exec postgres psql -U postgres -d market_data -c "SELECT COUNT(*) FROM marketdata;"
```

## 9. Logging

The pipeline uses structured JSON logging for:

* API extraction
* Retry attempts
* Validation results
* Dead-letter records
* VWAP processing
* Outlier detection
* Database connection
* Database loading
* Transaction rollback
* Batch completion
* Shutdown events

Invalid records are stored in:

```text
logs/dead_letter.jsonl
```

## 10. Project Structure

```text
Market-Data-Assessment/
│
├── api/
├── db/
├── etl/
│   ├── main.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── tests/
│
├── logs/
├── .env.example
├── .gitignore
├── docker-compose.yml
└── README.md
```

## 11. Current Implementation Status

### Implemented

* API extraction
* Retry handling
* Pydantic validation
* UTC timestamp normalization
* Dead-letter logging
* VWAP calculation
* Zero-volume handling
* IQR-based outlier detection
* PostgreSQL loading
* Duplicate protection
* Transaction rollback
* Structured logging
* Graceful shutdown
* Docker execution
* End-to-end pipeline execution

### Future Improvements

* Add database integration tests
* Add API mocking tests
* Add ingestion timestamp
* Add batch identifiers
* Add monitoring and alerting
* Add CI/CD using GitHub Actions
* Replace the continuous loop with a production scheduler
* Add data-quality dashboards
