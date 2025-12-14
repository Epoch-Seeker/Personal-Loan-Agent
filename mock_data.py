# mock_data.py
import json
import os
import random

DATA_FILE = "customers.json"

# ----------------------- CONSTANTS -----------------------
INTEREST_RATE = 12  # Standardized interest rate (12% p.a.)


# --- LOAD / SAVE -------------------------------------------------------------

def _load_customers_from_file():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    # Seed customers with address for KYC verification
    return [
        {
            "phone": "9999999991",
            "name": "Amit Sharma",
            "city": "Mumbai",
            "address": "Flat 12B, Sea View Apartments, Andheri West, Mumbai 400053",
            "existing_emi": 10000,
            "credit_score": 780,
            "pre_approved_limit": 500000,
        },
        {
            "phone": "9999999992",
            "name": "Priya Patel",
            "city": "Delhi",
            "address": "House No. 45, Sector 22, Dwarka, New Delhi 110077",
            "existing_emi": 5000,
            "credit_score": 820,
            "pre_approved_limit": 800000,
        },
        {
            "phone": "9999999993",
            "name": "Sunny Kumar",
            "city": "Pune",
            "address": "201 Harmony Heights, Baner Road, Pune 411045",
            "existing_emi": 12000,
            "credit_score": 750,
            "pre_approved_limit": 500000,
        },
        {
            "phone": "9999999994",
            "name": "Rajesh Verma",
            "city": "Bangalore",
            "address": "42, 3rd Cross, Indiranagar, Bangalore 560038",
            "existing_emi": 0,
            "credit_score": 650,
            "pre_approved_limit": 300000,
        },
        {
            "phone": "9999999995",
            "name": "Sneha Reddy",
            "city": "Hyderabad",
            "address": "Plot 78, Jubilee Hills Road No. 10, Hyderabad 500033",
            "existing_emi": 8000,
            "credit_score": 800,
            "pre_approved_limit": 700000,
        },
        {
            "phone": "9999999996",
            "name": "Vikram Singh",
            "city": "Chennai",
            "address": "15A, Anna Nagar East, Chennai 600102",
            "existing_emi": 15000,
            "credit_score": 720,
            "pre_approved_limit": 450000,
        },
        {
            "phone": "9999999997",
            "name": "Anita Desai",
            "city": "Kolkata",
            "address": "Flat 5C, Park Street Residency, Kolkata 700016",
            "existing_emi": 3000,
            "credit_score": 850,
            "pre_approved_limit": 1000000,
        },
        {
            "phone": "9999999998",
            "name": "Rahul Mehta",
            "city": "Ahmedabad",
            "address": "B-102, Swastik Heights, Navrangpura, Ahmedabad 380009",
            "existing_emi": 20000,
            "credit_score": 680,
            "pre_approved_limit": 350000,
        },
        {
            "phone": "9999999999",
            "name": "Kavita Joshi",
            "city": "Jaipur",
            "address": "56, Malviya Nagar, Jaipur 302017",
            "existing_emi": 6000,
            "credit_score": 760,
            "pre_approved_limit": 550000,
        },
        {
            "phone": "9999999900",
            "name": "Arjun Nair",
            "city": "Kochi",
            "address": "TC 12/456, Marine Drive, Ernakulam, Kochi 682031",
            "existing_emi": 0,
            "credit_score": 790,
            "pre_approved_limit": 600000,
        },
    ]


def _save_customers_to_file(customers):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(customers, f, indent=2)


CUSTOMERS = _load_customers_from_file()


# --- SALARY SLIP SIMULATION --------------------------------------------------

def extract_salary_from_slip(phone: str) -> int:
    """
    Simulate extracting monthly salary from uploaded salary slip PDF.
    In production, this would use OCR/Gemini to parse the actual PDF.
    For hackathon: returns a random salary between ₹50,000 - ₹1,50,000.
    """
    # Seed based on phone for consistent results per customer
    random.seed(hash(phone) % (2**32))
    salary = random.randint(50000, 150000)
    random.seed()  # Reset seed
    return salary


# --- ADDRESS GENERATION FOR NEW CUSTOMERS ------------------------------------

def _generate_random_address(city: str) -> str:
    """Generate a realistic-looking address for new customers."""
    street_types = ["Street", "Road", "Lane", "Avenue", "Marg", "Nagar"]
    building_types = ["Flat", "House No.", "Plot", "Unit"]
    areas = ["Sector 15", "Block A", "Phase 2", "West Wing", "East Block", "Central"]
    
    building = f"{random.choice(building_types)} {random.randint(1, 500)}"
    area = random.choice(areas)
    street = f"{random.choice(['Main', 'Park', 'Lake', 'Hill', 'Green'])} {random.choice(street_types)}"
    pincode = random.randint(100001, 999999)
    
    return f"{building}, {area}, {street}, {city} {pincode}"


# --- API ---------------------------------------------------------------------

def get_customer_by_phone(phone: str):
    for cust in CUSTOMERS:
        if cust["phone"] == phone:
            return cust
    return None


def create_new_customer(phone: str, name: str, city: str, address: str = None):
    """
    Create customer with address for KYC.
    Salary slip will be required during underwriting.
    """

    credit_score = random.randint(700, 850)            # Random fair-good score
    pre_limit = random.choice([300000, 400000, 500000]) # Give a base limit
    existing_emi = random.randint(0, 15000)             # Random EMI
    
    # Generate address if not provided
    if not address:
        address = _generate_random_address(city)

    new_customer = {
        "phone": phone,
        "name": name,
        "city": city,
        "address": address,
        "credit_score": credit_score,
        "pre_approved_limit": pre_limit,
        "existing_emi": existing_emi
    }

    CUSTOMERS.append(new_customer)
    _save_customers_to_file(CUSTOMERS)

    return new_customer
