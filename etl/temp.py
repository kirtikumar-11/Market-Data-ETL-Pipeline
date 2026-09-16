from etl.dead_letter import log_dead_letter

failed_record = {
    "instrument_id": "AAPL",
    "price": -100,
    "volume": 500,
    "timestamp": "2026-09-16T10:00:00"
}

log_dead_letter(
    failed_record,
    "Price must be greater than zero"
)