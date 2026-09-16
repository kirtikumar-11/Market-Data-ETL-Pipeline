import requests
from fastapi import HTTPException
from pydantic import BaseModel, EmailStr, Field, field_validator, ValidationError
from datetime import datetime, timezone
import psycopg2
import logging
import os
from dotenv import load_dotenv
from psycopg2.extras import execute_values
import signal
from threading import Event
import numpy as np
import json
from pathlib import Path
from pythonjsonlogger.json import JsonFormatter

logger = logging.getLogger("market-data-etl")
logger.setLevel(logging.INFO)

log_handler = logging.StreamHandler()

json_formatter = JsonFormatter(
    "%(asctime)s %(levelname)s %(name)s %(message)s"
)

log_handler.setFormatter(json_formatter)

logger.addHandler(log_handler)


class MarketData(BaseModel):
    instrument_id: str
    price: float = Field(gt=0)
    volume: int = Field(ge=0)
    timestamp: datetime
    vwap: float | None = None
    is_outlier: bool = False

def log_dead_letter(record, reason):
    dead_letter_file = Path("logs/dead_letter.jsonl")

    dead_letter_file.parent.mkdir(parents=True, exist_ok=True)

    dead_letter_entry = {
        "record": record,
        "reason": reason,
    }

    with dead_letter_file.open("a", encoding="utf-8") as file:
        file.write(json.dumps(dead_letter_entry, default=str) + "\n")

def extract_data():
    data = None
    for attempt in range(5):
        try:
            response = requests.get(API_URL, timeout=5)
            response.raise_for_status()
            data = response.json()
            logger.info(
                f"Successfully extracted {len(data)} records in {attempt + 1} attempt(s)"
            )
            return data

        except requests.exceptions.RequestException as e:
            if attempt < 4:
                delay = 2**attempt
                logger.warning(
                    f"Attempt {attempt + 1} failed: {e}. Retrying in {delay} seconds..."
                )
                shutdown_event.wait(delay)
                if shutdown_event.is_set():
                    return None
            else:
                logger.error(f"Extraction failed after 5 attempts: {e}")
            


def validate_data(data):
    validated_data = []
    rejected_count = 0
    for record in data:
        try:
            market_obj = MarketData(**record)
            if market_obj.timestamp.tzinfo is None:
                market_obj.timestamp = market_obj.timestamp.replace(tzinfo=timezone.utc)
            else:
                market_obj.timestamp = market_obj.timestamp.astimezone(timezone.utc)
            validated_data.append(market_obj)

        except ValidationError as e:            
            logger.warning(f"Invalid record skipped:{record} ")
            logger.warning(f"Validation Error: {e}")
            logger.warning(f"Before loeg dead letter function")
            log_dead_letter(record = record , reason=str(e))
            logger.warning(f"after  loeg dead letter function")
            rejected_count += 1
    logger.info(
        f"Validation complete: "
        f"Input: {len(data)}, "
        f"Valid: {len(validated_data)}, "
        f"Rejected: {rejected_count}"
    )
    return validated_data


def calculate_vwap(data):
    vwap_data = {}
    for record in data:
        instrument = record.instrument_id
        numerator = record.price * record.volume
        denominator = record.volume

        if instrument in vwap_data:
            vwap_data[instrument][0] += numerator
            vwap_data[instrument][1] += denominator
        else:
            vwap_data[instrument] = [numerator, denominator]
    vwap = {}
    for instrument, value in vwap_data.items():
            numerator, denominator = value
            if denominator == 0:
                vwap[instrument] = None
            else:
                vwap[instrument] = numerator / denominator

    for record in data:
        instrument = record.instrument_id
        record.vwap = vwap[instrument]
    return data



def detect_outliers(data):
    prices_by_instrument = {}
    outlier_count = 0
    price_ranges = {}

    # Group prices by instrument
    for record in data:
        instrument = record.instrument_id
        price = record.price

        if instrument in prices_by_instrument:
            prices_by_instrument[instrument].append(price)
        else:
            prices_by_instrument[instrument] = [price]

    # Calculate IQR bounds for each instrument
    for instrument, prices in prices_by_instrument.items():
        q1 = np.percentile(prices, 25)
        q3 = np.percentile(prices, 75)

        iqr = q3 - q1

        lower_bound = q1 - (1.5 * iqr)
        upper_bound = q3 + (1.5 * iqr)

        price_ranges[instrument] = [
            lower_bound,
            upper_bound
        ]

    # Identify outliers
    for record in data:
        instrument = record.instrument_id
        price = record.price

        lower_bound = price_ranges[instrument][0]
        upper_bound = price_ranges[instrument][1]

        record.is_outlier = (
            price < lower_bound or price > upper_bound
        )

        if record.is_outlier:
            outlier_count += 1

    logger.info(
        f"Outlier detection complete: "
        f"Total: {len(data)}, Outliers: {outlier_count}"
    )

    return data


def connect_db(host, port, dbname, user, password):
    for attempt in range(5):
        try:
            conn = psycopg2.connect(host=host, port=port, dbname=dbname, user=user, password=password)
            logger.info(f"Successfully Connected to the Database in {attempt+1} attempt(s)")
            return conn
        
        except psycopg2.Error as e:
            if attempt < 4:
                delay = 2**attempt
                logger.warning(
                    f" Database Connection Attempt {attempt + 1} failed: {e}. Retrying in {delay} seconds..."
                )
                shutdown_event.wait(delay)
                if shutdown_event.is_set():
                    return None
            else:
                logger.error(f"Database connection failed after 5 attempts: {e}")
                return None
                
    


def load_data(data, DB_CONFIG):
    conn = None
    cursor=None
    values = []
    insert_query = "INSERT INTO marketdata (instrument_id,price,volume,timestamp,vwap,is_outlier) Values %s ON CONFLICT (instrument_id,timestamp) DO NOTHING RETURNING id;"
    try:
        conn = connect_db(**DB_CONFIG)
        if conn is None:
            logger.error("Database connection not available")
            return False
        cursor = conn.cursor()
        for record in data:
            values.append(
                (
                    record.instrument_id,
                    record.price,
                    record.volume,
                    record.timestamp,
                    record.vwap,
                    bool(record.is_outlier),
                )
            )
        execute_values(cursor, insert_query, values)
        inserted_ids = cursor.fetchall()
        inserted_count = len(inserted_ids)
        duplicate_count = len(data) - inserted_count
        conn.commit()
        logger.info(
            "Database load complete",
            extra={
                "attempted_count": len(data),
                "inserted_count": inserted_count,
                "duplicate_count": duplicate_count,
                },
                )
        return True
    except Exception as e:
        logger.error(f"Database load failed for {len(data)} records: {e}")
        conn.rollback()
        logger.info("Transaction rolled back successfully.")
        return False
    finally:
        if cursor is not None:
            cursor.close()

        if conn is not None:
            conn.close()


load_dotenv()
API_URL = os.getenv("API_URL")

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT")),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}

required_vars = ["API_URL", "DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]


for var in required_vars:
    if not os.getenv(var):
        raise ValueError(f"Missing required environment variable: {var}")


def shutdown_handler(signum, frame):
    shutdown_event.set()
    logger.info("Shutdown signal received. Stopping ETL...")


shutdown_event = Event()
signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)


def main():
    while not shutdown_event.is_set():
        try:
            data = extract_data()
            if data is not None:
                validated_data = validate_data(data)
                validated_data = calculate_vwap(validated_data)
                validated_data = detect_outliers(validated_data)
                load_sucess = load_data(validated_data, DB_CONFIG)
                if not load_sucess:
                    logger.error("Database load failed. Stopping ETL Pipeline")
                    break

                
            else:
                logger.warning("No data fetched")
                logger.error("Extraction failed. Stopping ETL pipeline.")
                break
                
            logger.info(
                        "Batch processing complete",
                        extra={
                            "wait_seconds": 10,
                        },
                        )
            shutdown_event.wait(10)
        except Exception as e:
            logger.exception(f"Unexpected pipeline error: {e}")
            shutdown_event.wait(10)

if __name__ == "__main__":
    main()