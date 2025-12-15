from fastapi import APIRouter

router = APIRouter(prefix="/api/help", tags=["Help"])

@router.get("")
def get_help_content():
    return {
        "title": "LoanBuddy Help Center",
        "sections": [
            {
                "id": "how_it_works",
                "title": "How LoanBuddy Works",
                "items": [
                    "Select your loan purpose",
                    "Enter loan amount and tenure",
                    "Upload required documents",
                    "Eligibility check is done instantly",
                    "Get EMI details and sanction letter"
                ]
            },
            {
                "id": "documents",
                "title": "Required Documents",
                "items": [
                    "Latest Salary Slip (PDF or Image)",
                    "Government ID (Aadhaar / PAN)",
                    "Optional: Last 3 months bank statement"
                ]
            },
            {
                "id": "emi",
                "title": "EMI & Interest",
                "items": [
                    "Interest rates start from 14% p.a.",
                    "EMI depends on loan amount and tenure",
                    "No hidden charges"
                ]
            },
            {
                "id": "chatbot",
                "title": "Using the Chatbot",
                "items": [
                    "Ask: Am I eligible for a loan?",
                    "Ask: Calculate EMI for 5 lakh",
                    "Say: I have uploaded my salary slip",
                    "Ask: Show my loan status"
                ]
            },
            {
                "id": "faq",
                "title": "FAQs",
                "items": [
                    "Loan approval usually takes a few minutes",
                    "Loan amount may vary based on salary",
                    "Pre-closure is allowed"
                ]
            },
            {
                "id": "support",
                "title": "Support",
                "items": [
                    "Email: support@loanbuddy.ai",
                    "Helpline: 1800-XXX-XXXX",
                    "Support Hours: 9 AM – 6 PM"
                ]
            }
        ]
    }
