# mock_data.py
import json
import os
import random

DATA_FILE = "customers.json"


# --- LOAD / SAVE -------------------------------------------------------------

def _load_customers_from_file():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    # Seed customers (no salary concept)
    return [
        {
            "phone": "9999999991",
            "name": "Amit Sharma",
            "city": "Mumbai",
            "existing_emi": 10000,
            "credit_score": 750,
            "pre_approved_limit": 500000,   # fixed existing limit
        },
        {
            "phone": "9999999993",
            "name": "Sunny",
            "city": "Pune",
            "existing_emi": 12000,
            "credit_score": 780,
            "pre_approved_limit": 500000,
        },
    ]


def _save_customers_to_file(customers):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(customers, f, indent=2)


CUSTOMERS = _load_customers_from_file()


# --- API ---------------------------------------------------------------------

def get_customer_by_phone(phone: str):
    for cust in CUSTOMERS:
        if cust["phone"] == phone:
            return cust
    return None


def create_new_customer(phone: str, name: str, city: str):
    """
    Create customer WITHOUT salary logic.
    Salary slip will be required during underwriting.
    """

    credit_score = random.randint(700, 850)            # Random fair-good score
    pre_limit = random.choice([300000, 400000, 500000]) # Give a base limit
    existing_emi = random.randint(0, 15000)             # Random EMI

    new_customer = {
        "phone": phone,
        "name": name,
        "city": city,
        "credit_score": credit_score,
        "pre_approved_limit": pre_limit,
        "existing_emi": existing_emi
    }

    CUSTOMERS.append(new_customer)
    _save_customers_to_file(CUSTOMERS)

    return new_customer
