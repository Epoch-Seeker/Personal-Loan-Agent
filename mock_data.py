# mock_data.py
import json
import os
import random

DATA_FILE = "customers.json"


# --- LOAD / SAVE HELPERS ----------------------------------------------------

def _load_customers_from_file():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            # if file is corrupted, fall back to defaults
            pass
    # default seed data (2 existing customers)
    return [
        {
            "phone": "9999999991",
            "name": "Amit Sharma",
            "city": "Mumbai",
            "monthly_salary": 80000,
            "existing_emi": 10000,
            "credit_score": 750,
            "pre_approved_limit": 500000,
        },
        {
            "phone": "9999999993",
            "name": "Sunny",
            "city": "Pune",
            "monthly_salary": 90000, 
            "existing_emi": 12000,
            "credit_score": 780,
            "pre_approved_limit": 500000,
        },
    ]


def _save_customers_to_file(customers):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(customers, f, indent=2)


# in-memory list, initialised from disk
CUSTOMERS = _load_customers_from_file()


# --- PUBLIC API -------------------------------------------------------------

def get_customer_by_phone(phone: str):
    for cust in CUSTOMERS:
        if cust["phone"] == phone:
            return cust
    return None


def create_new_customer(phone: str, name: str, city: str, salary: int | None = None):
    """
    Create a new synthetic customer based on salary.

    - salary: monthly income (if None, assume 50,000)
    - credit_score: between 650 and 900 depending on salary
    - pre_approved_limit: 6x monthly salary (capped at 15L)
    - existing_emi: random 0–20% of salary
    """
    if salary is None:
        salary = 50000

    # credit score: 650 + (salary / 2000), capped at 900
    base_score = 650 + int(salary / 2000)
    credit_score = max(650, min(900, base_score))

    # pre-approved limit: 6x monthly salary, capped at 15L
    pre_limit = min(salary * 6, 1500000)

    # synthetic existing EMI: between 0 and 20% of salary
    existing_emi = int(salary * random.uniform(0, 0.2))

    new_customer = {
        "phone": phone,
        "name": name,
        "city": city,
        "monthly_salary": salary, 
        "existing_emi": existing_emi,
        "credit_score": credit_score,
        "pre_approved_limit": pre_limit,
    }

    # add to in-memory list
    CUSTOMERS.append(new_customer)
    # and persist to disk
    _save_customers_to_file(CUSTOMERS)

    return new_customer
