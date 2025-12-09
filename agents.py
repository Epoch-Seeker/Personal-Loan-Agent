# agents.py
import math
import os
import re
from mock_data import get_customer_by_phone, create_new_customer

# ----------------------- HELPERS -----------------------

def check_salary_slip_exists(phone: str) -> bool:
    """Check if salary slip PDF exists."""
    if not phone:
        return False
    return os.path.exists(f"uploads/{phone}_salary_slip.pdf")


def fetch_general_offers():
    return [
        "🌟 **Diwali Bonanza:** Zero Processing Fee on personal loans.",
        "📉 **Auto-Pay Special:** 0.5% interest rate discount with Auto-Debit.",
        "⚡ **Express Loan:** Instant approval — disbursal in 10 minutes."
    ]


def calculate_emi(principal, rate_annual, tenure_months):
    if tenure_months == 0:
        return 0
    r = rate_annual / 1200
    try:
        emi = principal * r * (1 + r) ** tenure_months / ((1 + r) ** tenure_months - 1)
        return round(emi, 2)
    except:
        return 0


def parse_loan_amount(text: str) -> int:
    """Convert text like '5 lakh', '2.5L', '40k', '200000' → int rupees"""
    if not text:
        return 0
    s = text.lower().replace(",", " ")
    s = " ".join(s.split())

    if m := re.search(r"(\d+\.?\d*)\s*(lakh|lac|lacs)", s):
        return int(float(m.group(1)) * 100000)

    if m := re.search(r"(\d+\.?\d*)\s*(k|thousand)", s):
        return int(float(m.group(1)) * 1000)

    nums = re.findall(r"\d+", s)
    return int(nums[-1]) if nums else 0


# ----------------------- VERIFICATION / REGISTRATION -----------------------

def verification_agent(phone):
    user = get_customer_by_phone(phone)
    if user:
        return {
            "status": "VERIFIED",
            "name": user["name"],
            "city": user["city"],
            "limit": user["pre_approved_limit"]
        }
    return {"status": "FAILED"}


def register_agent(phone, name, city):
    """Create customer without salary field"""
    user = create_new_customer(phone, name, city)
    return {
        "status": "REGISTERED",
        "name": user["name"],
        "city": user["city"],
        "limit": user["pre_approved_limit"],
        "credit_score": user["credit_score"],
        "existing_emi": user["existing_emi"]
    }


# ----------------------- UNDERWRITING -----------------------

def underwriting_agent(phone, loan_amount, tenure_months=12, salary_slip_uploaded=False):
    """
    Rules:
    ✔ If credit_score < 700 → HARD_REJECT
    ✔ If amount <= limit → APPROVE instantly
    ✔ If limit < amount <= 2*limit → NEED SALARY SLIP
    ✔ If salary slip uploaded → APPROVE
    ✔ If amount > 2*limit → SOFT_REJECT with fallback offer
    """

    user = get_customer_by_phone(phone)
    if not user:
        return {"status": "ERROR", "reason": "Customer not found"}

    limit = user["pre_approved_limit"]
    score = user["credit_score"]

    # 1. Score based rejection
    if score < 700:
        return {"status": "HARD_REJECT", "reason": f"Low credit score ({score})"}

    # 2. Above double the limit → soft reject
    if loan_amount > 2 * limit:
        return {
            "status": "SOFT_REJECT",
            "fallback_offer": limit,
            "reason": "Requested amount exceeds 2x eligibility"
        }

    # 3. Instant approval path
    if loan_amount <= limit:
        return {
            "status": "APPROVED",
            "new_emi": calculate_emi(loan_amount, 14, tenure_months),
            "details": "Approved within pre-approved limit"
        }

    # 4. Over limit → need slip
    if not salary_slip_uploaded:
        return {"status": "NEEDS_DOCS", "reason": "Upload salary slip for income verification"}

    # 5. Once slip uploaded → Approve without salary evaluation
    return {
        "status": "APPROVED",
        "new_emi": calculate_emi(loan_amount, 14, tenure_months),
        "details": "Approved after document verification"
    }
