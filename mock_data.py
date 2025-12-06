# mock_data.py

CUSTOMERS = [
    {
        "phone": "9999999991",
        "name": "Amit Sharma",
        "city": "Mumbai",
        "monthly_salary": 80000,
        "existing_emi": 10000,
        "credit_score": 750,
        "pre_approved_limit": 500000
    },
    {
        "phone": "9999999992",
        "name": "Priya Singh",
        "city": "Delhi",
        "monthly_salary": 40000,
        "existing_emi": 5000,
        "credit_score": 650, # Low score (Should be rejected)
        "pre_approved_limit": 200000
    },
    {
        "phone": "9999999993",
        "name": "Rahul Verma",
        "city": "Bangalore",
        "monthly_salary": 150000,
        "existing_emi": 20000,
        "credit_score": 800,
        "pre_approved_limit": 1000000
    },
    # ... We can add 7 more later
]

def get_customer_by_phone(phone):
    for cust in CUSTOMERS:
        if cust["phone"] == phone:
            return cust
    return None