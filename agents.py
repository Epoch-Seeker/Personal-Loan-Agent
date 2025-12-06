# agents.py
import os
import math
from mock_data import get_customer_by_phone

# --- HELPER FUNCTIONS (Mocking External APIs) ---

def check_salary_slip_exists(phone):
    """
    Checks if a file named '{phone}_salary_slip.pdf' exists in the uploads folder.
    """
    expected_filename = f"uploads/{phone}_salary_slip.pdf"
    if os.path.exists(expected_filename):
        return True
    return False

def fetch_credit_score(phone):
    """Simulates fetching from a Credit Bureau API"""
    user = get_customer_by_phone(phone)
    if user:
        return user["credit_score"]
    return 0

def fetch_pre_approved_limit(phone):
    """Simulates fetching from an Offer Mart Server"""
    user = get_customer_by_phone(phone)
    if user:
        return user["pre_approved_limit"]
    return 0

def calculate_emi(principal, rate_annual, tenure_months):
    """
    Calculates Monthly EMI.
    Rate should be annual % (e.g., 12 for 12%).
    """
    if tenure_months == 0: return 0
    monthly_rate = rate_annual / (12 * 100)
    
    # Formula: P * r * (1+r)^n / ((1+r)^n - 1)
    try:
        emi = (principal * monthly_rate * math.pow(1 + monthly_rate, tenure_months)) / \
              (math.pow(1 + monthly_rate, tenure_months) - 1)
        return round(emi, 2)
    except ZeroDivisionError:
        return 0

# --- WORKER AGENT 1: VERIFICATION AGENT ---

def verification_agent(phone):
    """
    Checks if customer exists in CRM (Mock Data).
    Returns: Dict with status and details.
    """
    user = get_customer_by_phone(phone)
    if user:
        return {
            "status": "VERIFIED",
            "name": user["name"],
            "city": user["city"],
            "message": f"User verified: {user['name']} from {user['city']}."
        }
    else:
        return {
            "status": "FAILED",
            "message": "User not found in our records."
        }

# --- WORKER AGENT 2: UNDERWRITING AGENT ---

def underwriting_agent(phone, loan_amount, tenure_months=12, salary_slip_uploaded=False):
    """
    The BRAIN. Decides if a loan is approved based on:
    1. Credit Score (>700)
    2. Loan Amount vs Pre-approved Limit
    3. Salary/EMI ratio (if high loan amount)
    """
    
    # 1. Fetch Data
    user = get_customer_by_phone(phone)
    if not user:
        return {"status": "ERROR", "reason": "User not found"}
        
    credit_score = fetch_credit_score(phone)
    limit = fetch_pre_approved_limit(phone)
    
    # 2. Rule: Credit Score Check
    if credit_score < 700:
        return {
            "status": "REJECTED", 
            "reason": f"Credit score {credit_score} is below 700."
        }

    # 3. Rule: Instant Approval (Amount <= Limit)
    if loan_amount <= limit:
        return {
            "status": "APPROVED",
            "reason": "Amount is within pre-approved limit."
        }
    
    # 4. Rule: Hard Rejection (Amount > 2x Limit)
    if loan_amount > (2 * limit):
        return {
            "status": "REJECTED",
            "reason": f"Amount {loan_amount} exceeds 2x limit of {limit}."
        }

    # 5. Rule: Conditional Approval (Needs Salary Slip)
    # Amount is between Limit and 2x Limit
    if not salary_slip_uploaded:
        return {
            "status": "NEEDS_DOCS",
            "reason": "Loan exceeds pre-approved limit. Please upload salary slip."
        }
    
    # 6. Rule: Verify Affordability (The "Underwriting" Math)
    # Assume interest rate of 14% for personal loans
    current_emi = user["existing_emi"]
    new_emi = calculate_emi(loan_amount, 14, tenure_months)
    total_obligation = current_emi + new_emi
    
    # Max EMI allowed is 50% of monthly salary
    max_allowed_emi = user["monthly_salary"] * 0.50
    
    if total_obligation <= max_allowed_emi:
        return {
            "status": "APPROVED",
            "reason": f"EMI ({new_emi}) is affordable. Total obligation: {total_obligation}",
            "new_emi": new_emi
        }
    else:
        return {
            "status": "REJECTED",
            "reason": f"High Debt-to-Income Ratio. Total EMI {total_obligation} > 50% of Salary."
        }