# agents.py
import math
import os
import re
from mock_data import get_customer_by_phone, create_new_customer, extract_salary_from_slip, INTEREST_RATE

# ----------------------- CONSTANTS -----------------------
# Use centralized interest rate from mock_data
ANNUAL_INTEREST_RATE = INTEREST_RATE  # 12% p.a. (standardized)


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
        "⚡ **Express Loan:** Instant approval — disbursal in 10 minutes.",
        "💳 **Festive Offer:** Get additional ₹50,000 credit limit on timely repayment."
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
    """
    Verify customer KYC details including phone and address.
    Returns customer details for address confirmation.
    """
    user = get_customer_by_phone(phone)
    if user:
        return {
            "status": "VERIFIED",
            "name": user["name"],
            "city": user["city"],
            "address": user.get("address", "Address not on file"),
            "limit": user["pre_approved_limit"],
            "credit_score": user["credit_score"]
        }
    return {"status": "FAILED"}


def register_agent(phone, name, city, address=None):
    """Create customer with address for KYC verification"""
    user = create_new_customer(phone, name, city, address)
    return {
        "status": "REGISTERED",
        "name": user["name"],
        "city": user["city"],
        "address": user["address"],
        "limit": user["pre_approved_limit"],
        "credit_score": user["credit_score"],
        "existing_emi": user["existing_emi"]
    }


# ----------------------- UNDERWRITING -----------------------

def underwriting_agent(phone, loan_amount, tenure_months=12, salary_slip_uploaded=False):
    """
    Enhanced Underwriting Rules:
    ✔ If credit_score < 700 → HARD_REJECT
    ✔ If amount <= limit → APPROVE instantly
    ✔ If limit < amount <= 2*limit → NEED SALARY SLIP
    ✔ If salary slip uploaded → Check EMI ≤ 50% of salary
       - If EMI ≤ 50% salary → APPROVE
       - If EMI > 50% salary → SOFT_REJECT with lower offer
    ✔ If amount > 2*limit → SOFT_REJECT with fallback offer
    """

    user = get_customer_by_phone(phone)
    if not user:
        return {"status": "ERROR", "reason": "Customer not found"}

    limit = user["pre_approved_limit"]
    score = user["credit_score"]

    # 1. Score based rejection
    if score < 700:
        return {
            "status": "HARD_REJECT", 
            "reason": f"Low credit score ({score}). We need a minimum score of 700 for loan approval."
        }

    # 2. Above double the limit → soft reject
    if loan_amount > 2 * limit:
        return {
            "status": "SOFT_REJECT",
            "fallback_offer": limit,
            "reason": "Requested amount exceeds 2x your eligibility limit",
            "persuasion": f"I understand you need ₹{loan_amount}, but based on your profile, I can offer you ₹{limit} instantly. This can still help with your immediate needs, and we can increase your limit after 6 months of good repayment!"
        }

    # 3. Instant approval path (within pre-approved limit)
    if loan_amount <= limit:
        emi = calculate_emi(loan_amount, ANNUAL_INTEREST_RATE, tenure_months)
        return {
            "status": "APPROVED",
            "new_emi": emi,
            "interest_rate": ANNUAL_INTEREST_RATE,
            "details": "Approved within pre-approved limit"
        }

    # 4. Over limit but within 2x → need salary slip
    if not salary_slip_uploaded:
        return {
            "status": "NEEDS_DOCS", 
            "reason": "Upload salary slip for income verification",
            "message": "Since you're requesting above your instant limit, I'll need to verify your income. Please upload your latest salary slip."
        }

    # 5. Salary slip uploaded → Apply EMI ≤ 50% of salary rule
    extracted_salary = extract_salary_from_slip(phone)
    emi = calculate_emi(loan_amount, ANNUAL_INTEREST_RATE, tenure_months)
    max_allowed_emi = extracted_salary * 0.5  # 50% of salary rule
    
    if emi <= max_allowed_emi:
        # EMI is within 50% of salary → APPROVE
        return {
            "status": "APPROVED",
            "new_emi": emi,
            "interest_rate": ANNUAL_INTEREST_RATE,
            "salary_verified": extracted_salary,
            "details": f"Approved after income verification. Your salary of ₹{extracted_salary} supports this EMI."
        }
    else:
        # EMI exceeds 50% of salary → Calculate max affordable amount
        # Reverse calculate: What amount gives EMI = 50% of salary?
        max_emi = max_allowed_emi
        r = ANNUAL_INTEREST_RATE / 1200
        if r > 0:
            max_affordable_amount = int(max_emi * ((1 + r) ** tenure_months - 1) / (r * (1 + r) ** tenure_months))
        else:
            max_affordable_amount = int(max_emi * tenure_months)
        
        # Ensure we don't offer more than 2x limit
        max_affordable_amount = min(max_affordable_amount, 2 * limit)
        
        return {
            "status": "SOFT_REJECT",
            "fallback_offer": max_affordable_amount,
            "reason": f"EMI (₹{emi}) exceeds 50% of your verified salary (₹{extracted_salary})",
            "salary_verified": extracted_salary,
            "max_emi_allowed": max_allowed_emi,
            "persuasion": f"Based on your salary of ₹{extracted_salary}, I can approve up to ₹{max_affordable_amount} to keep your EMI manageable at ₹{calculate_emi(max_affordable_amount, ANNUAL_INTEREST_RATE, tenure_months)}. This ensures comfortable repayment!"
        }
