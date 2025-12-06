# test_logic.py
from agents import underwriting_agent, verification_agent

print("--- Test 1: High Credit Score, Low Amount (Should Approve) ---")
# Amit (Score 750, Limit 5L). Asking for 1L.
result = underwriting_agent("9999999991", 100000)
print(result)

print("\n--- Test 2: Low Credit Score (Should Reject) ---")
# Priya (Score 650). Asking for anything.
result = underwriting_agent("9999999992", 50000)
print(result)

print("\n--- Test 3: High Amount (Needs Salary Slip) ---")
# Amit (Limit 5L). Asking for 8L (Between 1x and 2x).
# First try: No slip uploaded
result = underwriting_agent("9999999991", 800000, salary_slip_uploaded=False)
print("No Slip:", result)

# Second try: Slip uploaded
result = underwriting_agent("9999999991", 800000, salary_slip_uploaded=True)
print("With Slip:", result)