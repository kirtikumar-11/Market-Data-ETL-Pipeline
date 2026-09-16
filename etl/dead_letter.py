import json
from pathlib import Path


def log_dead_letter(record, reason):
    dead_letter_file = Path("logs/dead_letter.jsonl")

    dead_letter_file.parent.mkdir(parents=True, exist_ok=True)

    dead_letter_entry = {
        "record": record,
        "reason": reason,
    }

    with dead_letter_file.open("a", encoding="utf-8") as file:
        file.write(json.dumps(dead_letter_entry, default=str) + "\n")