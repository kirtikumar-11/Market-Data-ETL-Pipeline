from datetime import datetime, timezone

from main import (
    MarketData,
    validate_data,
    calculate_vwap,
    detect_outliers,
)


def test_validate_data_accepts_valid_record():
    data = [
        {
            "instrument_id": "AAPL",
            "price": 150.0,
            "volume": 10,
            "timestamp": "2026-01-01T10:00:00",
        }
    ]

    result = validate_data(data)

    assert len(result) == 1
    assert isinstance(result[0], MarketData)
    assert result[0].instrument_id == "AAPL"
    assert result[0].price == 150.0


def test_validate_data_rejects_invalid_price():
    data = [
        {
            "instrument_id": "AAPL",
            "price": -10,
            "volume": 10,
            "timestamp": "2026-01-01T10:00:00",
        }
    ]

    result = validate_data(data)

    assert len(result) == 0


def test_validate_data_converts_timestamp_to_utc():
    data = [
        {
            "instrument_id": "AAPL",
            "price": 150.0,
            "volume": 10,
            "timestamp": "2026-01-01T10:00:00",
        }
    ]

    result = validate_data(data)

    assert result[0].timestamp.tzinfo == timezone.utc


def test_calculate_vwap():
    data = [
        MarketData(
            instrument_id="AAPL",
            price=100,
            volume=10,
            timestamp=datetime.now(timezone.utc),
        ),
        MarketData(
            instrument_id="AAPL",
            price=200,
            volume=20,
            timestamp=datetime.now(timezone.utc),
        ),
    ]

    result = calculate_vwap(data)

    expected_vwap = ((100 * 10) + (200 * 20)) / (10 + 20)

    assert result[0].vwap == expected_vwap
    assert result[1].vwap == expected_vwap


def test_detect_outliers():
    data = [
        MarketData(
            instrument_id="AAPL",
            price=100,
            volume=10,
            timestamp=datetime.now(timezone.utc),
        ),
        MarketData(
            instrument_id="AAPL",
            price=101,
            volume=10,
            timestamp=datetime.now(timezone.utc),
        ),
        MarketData(
            instrument_id="AAPL",
            price=102,
            volume=10,
            timestamp=datetime.now(timezone.utc),
        ),
        MarketData(
            instrument_id="AAPL",
            price=1000,
            volume=10,
            timestamp=datetime.now(timezone.utc),
        ),
    ]

    result = detect_outliers(data)

    assert result[-1].is_outlier

def test_invalid_record_is_logged_to_dead_letter(tmp_path, monkeypatch):
    import main

    dead_letter_file = tmp_path / "dead_letter.jsonl"

    monkeypatch.setattr(
        main,
        "log_dead_letter",
        lambda record, reason: dead_letter_file.write_text(
            f"{record}|{reason}\n"
        ),
    )

    data = [
        {
            "instrument_id": "AAPL",
            "price": -10,
            "volume": 10,
            "timestamp": "2026-01-01T10:00:00",
        }
    ]

    result = validate_data(data)

    assert len(result) == 0
    assert dead_letter_file.exists()

    content = dead_letter_file.read_text()

    assert "AAPL" in content
    assert "price" in content

def test_calculate_vwap_with_zero_volume():
    data = [
        MarketData(
            instrument_id="AAPL",
            price=100,
            volume=0,
            timestamp=datetime.now(timezone.utc),
        )
    ]

    result = calculate_vwap(data)

    assert result[0].vwap is None