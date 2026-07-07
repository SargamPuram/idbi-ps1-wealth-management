"""In-memory customer data store. Loads data/customers.json once at startup."""
import json
from pathlib import Path
from threading import Lock

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "customers.json"

_lock = Lock()
_customers_by_id = {}
_customers_list = []


def load():
    global _customers_by_id, _customers_list
    with _lock:
        if _customers_list:
            return
        if not DATA_PATH.exists():
            raise FileNotFoundError(
                f"{DATA_PATH} not found. Run scripts/generate_data.py first to generate "
                f"the 5,000 synthetic customer profiles."
            )
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        _customers_list = data
        _customers_by_id = {c["customer_id"]: c for c in data}


def get_customer(customer_id: str):
    load()
    return _customers_by_id.get(customer_id)


def all_customers():
    load()
    return _customers_list


def count():
    load()
    return len(_customers_list)


def sample_ids(n=10):
    load()
    return [c["customer_id"] for c in _customers_list[:n]]
