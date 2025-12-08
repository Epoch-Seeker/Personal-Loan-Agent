# agents.py
import math
import os
import re
from mock_data import get_customer_by_phone, create_new_customer

# --- HELPER FUNCTIONS ---

def check_salary_slip_exists(phone: str) -> bool:
    """Checks if a file named '{phone}_salary_slip.pdf' exists in uploads/."""
    if not phone:
        return False
    expected_filename = os.path.join("uploads", f"{phone}_salary_slip.pdf")
    return os.path.exists(expected_filename)

def fetch_general_offers():
    """Returns list of offers for the Master Agent's casual chat."""
    return [
        "🌟 **Diwali Bonanza:** Zero Processing Fee on all personal loans.",
        "📉 **Auto-Pay Special:** 0.5% interest rate reduction for auto-debit users.",
        "⚡ **Express Loan:** Money in your account in 10 minutes."
    ]

def calculate_emi(principal, rate_annual, tenure_months):
    """Calculates Monthly EMI."""
    if tenure_months == 0: return 0
    monthly_rate = rate_annual / (12 * 100)
    try:
        emi = (principal * monthly_rate * math.pow(1 + monthly_rate, tenure_months)) / \
              (math.pow(1 + monthly_rate, tenure_months) - 1)
        return round(emi, 2)
    except:
        return 0
    
def parse_loan_amount(text: str) -> int:
    """
    Parse human text like:
      - '2 lakh', '3 lacs', '1.5 lakh'
      - '50 thousand', '40k'
      - '200000'
    Returns amount in rupees, or 0 if not understood.
    """
    if not text:
        return 0

    import re
    s = text.lower().replace(",", " ")
    s = " ".join(s.split())  # normalize spaces

    # 1) lakh / lac
    m = re.search(r"(\d+(\.\d+)?)\s*(lakh|lac|lacs)", s)
    if m:
        val = float(m.group(1))
        return int(val * 100000)

    # 2) thousand / k
    m = re.search(r"(\d+(\.\d+)?)\s*(thousand|k)", s)
    if m:
        val = float(m.group(1))
        return int(val * 1000)

    # 3) plain big number (5+ digits)
    nums = re.findall(r"\d+", s)
    for n in reversed(nums):
        if len(n) >= 5:  # 10000 and above
            return int(n)

    # 4) fallback – last number if nothing else
    if nums:
        return int(nums[-1])

    return 0

# --- 1. VERIFICATION & REGISTRATION AGENTS ---

def verification_agent(phone):
    """Checks if user exists. Returns details if found."""
    user = get_customer_by_phone(phone)
    if user:
        return {
            "status": "VERIFIED",
            "name": user["name"],
            "city": user["city"],
            "limit": user["pre_approved_limit"],
            "message": f"User verified: {user['name']}."
        }
    return {"status": "FAILED", "message": "User not found."}

def register_agent(phone, name, city, salary=None):
    """
    Registers a new user on the fly.

    salary: monthly salary in rupees (int). If None, we assume a default.
    """
    user = create_new_customer(phone, name, city, salary)
    # print(user)
    return {
        "status": "REGISTERED",
        "name": user["name"],
        "city": user["city"],
        "limit": user["pre_approved_limit"],
        "existing_emi": user["existing_emi"],
        "credit_score": user["credit_score"],
        "salary": user["monthly_salary"],
    }


# --- 2. UNDERWRITING AGENT ---
def underwriting_agent(phone, loan_amount, tenure_months=12, salary_slip_uploaded=False):
    """
    Underwriting logic:

    1) If credit score < 700           -> HARD_REJECT
    2) If amount  > 2 * limit          -> SOFT_REJECT (offer limit instead)
    3) If amount <= limit              -> APPROVED instantly
    4) If limit < amount <= 2 * limit  -> 
         - if no salary slip           -> NEEDS_DOCS
         - if slip present:
             * compute EMI
             * APPROVED only if EMI <= 50% of salary
             * else HARD_REJECT
    """

    user = get_customer_by_phone(phone)
    if not user:
        return {"status": "ERROR", "reason": "Customer not found"}

    limit = user["pre_approved_limit"]
    score = user["credit_score"]

    # Try to read monthly salary from mock data (adjust key to match your mock_data.py)
    salary = user.get("salary") or user.get("monthly_salary") or 0

    # 1) Credit score rule
    if score < 700:
        return {
            "status": "HARD_REJECT",
            "reason": f"Credit score ({score}) does not meet the minimum criteria of 700."
        }

    # 2) Amount > 2x limit -> soft reject with fallback
    if loan_amount > (2 * limit):
        return {
            "status": "SOFT_REJECT",
            "reason": "Requested amount exceeds 2× the pre-approved limit.",
            "fallback_offer": limit,
        }

    # 3) Instant approval path: amount within limit
    if loan_amount <= limit:
        new_emi = calculate_emi(loan_amount, 14, tenure_months)
        return {
            "status": "APPROVED",
            "new_emi": new_emi,
            "compliance": "Compliance Status: Passed (RBI Checks Cleared)",
            "details": f"Loan of {loan_amount} approved at 14% p.a. (within pre-approved limit).",
        }

    # 4) Conditional path: limit < amount <= 2x limit
    #    First time: ask for documents
    if not salary_slip_uploaded:
        return {
            "status": "NEEDS_DOCS",
            "reason": "Loan exceeds pre-approved limit. Income verification (salary slip) required."
        }

    # Salary slip is uploaded: check EMI vs salary
    new_emi = calculate_emi(loan_amount, 14, tenure_months)

    # If salary is known, enforce EMI <= 50% of salary
    if salary and new_emi > 0.5 * salary:
        return {
            "status": "HARD_REJECT",
            "reason": (
                f"Expected EMI ({new_emi}) exceeds 50% of declared salary ({salary}). "
                "Cannot approve requested amount."
            ),
        }

    # Conditional approval success
    return {
        "status": "APPROVED",
        "new_emi": new_emi,
        "compliance": "Compliance Status: Passed (RBI + income checks cleared)",
        "details": f"Loan of {loan_amount} approved at 14% p.a. after income verification.",
    }

def parse_salary(text: str) -> int:
    text = text.lower().strip().replace(",", "").replace(" ", "")

    # Case 1: Pure number → 50000, 120000 etc
    if re.fullmatch(r"\d+", text):
        return int(text)

    # Case 2: Formats like 90k, 100k, 75k
    match_k = re.match(r"(\d+(\.\d+)?)(k)", text)
    if match_k:
        return int(float(match_k.group(1)) * 1000)

    # Case 3: Formats like 1.5l, 2lakh, 3lakhs, 1.2lac
    match_lakh = re.match(r"(\d+(\.\d+)?)(l|lac|lakh|lakhs)", text)
    if match_lakh:
        return int(float(match_lakh.group(1)) * 100000)

    # Case 4: Extract digits only (fallback)
    nums = re.findall(r"\d+(\.\d+)?", text)
    if nums:
        return int(float(nums[0]) * 100000) if "l" in text else int(float(nums[0]))

    return 0

