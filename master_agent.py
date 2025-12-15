# ===============================================
# master_agent.py  (Enhanced with KYC & Sales Logic)
# ===============================================

import os, re, json, operator
from typing import TypedDict, Annotated, Optional
from dotenv import load_dotenv
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langgraph.graph import StateGraph, END

from agents import (
    verification_agent,
    underwriting_agent,
    register_agent,
    fetch_general_offers,
    calculate_emi,
    parse_loan_amount,
    check_salary_slip_exists,
    ANNUAL_INTEREST_RATE
)
from pdf_generator import create_sanction_letter
from mock_data import get_customer_by_phone, INTEREST_RATE

# ----------------------------------------------------------
# LLM
# ----------------------------------------------------------
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

# ----------------------------------------------------------
# Agent State
# ----------------------------------------------------------
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    customer_phone: Optional[str]
    customer_name: Optional[str]
    customer_address: Optional[str]  # Added for KYC
    loan_amount: int
    loan_tenure: int
    loan_purpose: Optional[str]  # Added for needs analysis
    step: str
    offered_discount: bool
    final_decision: Optional[dict]

def get_history_string(messages, limit=50):
    s=""
    for m in messages[-limit:]:
        role="User" if isinstance(m,HumanMessage) else "AI"
        s+=f"{role}: {m.content}\n"
    return s

# ----------------------------------------------------------
# Structured Response Helpers (for Frontend Card Rendering)
# ----------------------------------------------------------

def create_loan_offer_card(pre_approved_limit: int, interest_rate: float = 12, max_tenure: int = 60) -> str:
    """Create structured tag for loan offer card."""
    return f'[LOAN_OFFER]{{"preApprovedLimit":{pre_approved_limit},"interestRate":{interest_rate},"maxTenure":{max_tenure}}}[/LOAN_OFFER]'

def create_loan_summary_card(amount: int, interest_rate: float, tenure: int, emi: float) -> str:
    """Create structured tag for loan summary card."""
    return f'[LOAN_SUMMARY]{{"amount":{amount},"interestRate":{interest_rate},"tenure":{tenure},"emi":{emi:.2f}}}[/LOAN_SUMMARY]'

def create_approval_card(name: str, amount: int, emi: float, pdf_link: str) -> str:
    """Create structured tag for approval card."""
    import json
    data = {"name": name, "amount": amount, "emi": f"{emi:.2f}", "pdfLink": pdf_link}
    return f'[APPROVAL]{json.dumps(data)}[/APPROVAL]'

def create_rejection_card(reason: str, credit_score: int = None) -> str:
    """Create structured tag for rejection card."""
    import json
    data = {"reason": reason}
    if credit_score:
        data["creditScore"] = credit_score
    return f'[REJECTION]{json.dumps(data)}[/REJECTION]'

# add near other imports
_LOAN_KEYWORDS = {"lakh", "lac", "loan", "rupee", "rupees", "thousand", "amount", "emi", "borrow"}

def _looks_like_amount_or_noise(text: str) -> bool:
    """Check if text looks like a loan amount or monetary value."""
    t = text.lower().strip()
    
    # Check for digits (amounts)
    if any(ch.isdigit() for ch in t):
        return True
    
    # Check for loan keywords - use word boundary matching to avoid false positives
    # e.g., don't match 'k' in 'Kumar' or 'lac' in 'place'
    for kw in _LOAN_KEYWORDS:
        # Use word boundaries to match whole words only
        if re.search(r'\b' + re.escape(kw) + r'\b', t):
            return True
    
    return False

def _is_probable_name(text: str) -> bool:
    """Check if given input looks like a real person's name."""
    if not text:
        return False

    raw = text.strip()
    low = raw.lower()

    # Reject single-word greetings / commands
    bad_tokens = {"hi", "hii", "hey", "hello", "yo", "ok", "resume", "start new", "restart", "cancel"}
    if low in bad_tokens:
        return False

    # Reject too small / too large
    if len(raw) < 2 or len(raw) > 60:
        return False

    # No digits allowed
    if any(ch.isdigit() for ch in raw):
        return False

    # Reject loan or money related input - use word boundary matching
    loan_keywords = {"loan", "emi", "amount", "borrow", "rupee", "₹", "salary", "limit"}
    for kw in loan_keywords:
        if re.search(r'\b' + re.escape(kw) + r'\b', low):
            return False

    # Must contain alphabet characters only (spaces, dots, hyphens allowed for names)
    if not re.fullmatch(r"[a-zA-Z\s.'-]{2,60}", raw):
        return False
    
    # Must have at least one letter
    if not any(ch.isalpha() for ch in raw):
        return False

    # If all checks passed => valid probable name
    return True


def _is_probable_city(text: str) -> bool:
    """Simple city validation: no digits, not loan text, short-ish."""
    if not text or len(text.strip()) < 2 or len(text) > 50:
        return False
    if any(ch.isdigit() for ch in text):
        return False
    low = text.lower()
    if any(kw in low for kw in _LOAN_KEYWORDS):
        return False
    # some city names contain spaces or hyphens, that's OK
    return True



# ==========================================================
# ================  MASTER CONTROLLER NODE  ================
# ==========================================================
def master_node(state: AgentState):
    """
    Deterministic-first controller (no salary fields).
    Tools: verify, register, underwrite, create_pdf
    """
    # If no messages yet => friendly greeting
    if not state.get('messages'):
        return {
            "messages": [
                AIMessage(content=(
                    "👋 Hi! I'm your Tata Capital loan assistant.\n"
                    "You can share your **phone number** to start the loan conversation"
                ))
            ],
            "step": "greet"
        }

    msg_raw = state['messages'][-1].content
    msg = (msg_raw or "").lower()
    step = state.get('step', 'greet')
    history_context = get_history_string(state['messages'], limit=50)

    print(f"--- MASTER: Step '{step}' | User said: {msg[:60]} ---")

    # -------- Global interrupts --------
    if any(w in msg for w in ["reset", "restart", "cancel"]):
        return {
            "messages": [AIMessage(content="🔄 Conversation reset. How can I help you today?")],
            "step": "greet",
            "loan_amount": 0,
            "customer_phone": None,
            "customer_name": None,
            "offered_discount": False,
            "final_decision": {}
        }

    # -------- Offers (deterministic) --------
    if "offer" in msg and "letter" not in msg:
        offers = fetch_general_offers()
        offers_text = "🎁 **Current Offers Available:**\n\n" + "\n\n".join(offers)
        offers_text += "\n\n💼 Would you like to apply for a personal loan?"
        return {"messages": [AIMessage(content=offers_text)], "step": "greet"}

    # -------- Phase: greet (deterministic intent checks) --------
    if step == "greet":
        # phone typed directly -> verify ONLY if exactly 10 digits
        digits_only = re.sub(r"\D", "", msg)
        if len(digits_only) >= 8:  # User is trying to enter a phone number
            if len(digits_only) == 10:
                return {"step": "verifying"}
            else:
                return {
                    "messages": [AIMessage(content=f"I need a valid **10-digit phone number**. You entered {len(digits_only)} digits. Please enter your complete phone number.")],
                    "step": "waiting_for_phone"
                }

        # greeting small talk
        greetings = ["hi", "hello", "hey", "greetings"]
        if any(msg.strip().startswith(g) for g in greetings) and len(msg) < 20:
            return {
                "messages": [AIMessage(content="Hello! Welcome to Tata Capital. I can help with personal loans — would you like to check offers or apply now?")],
                "step": "greet"
            }

        # Direct yes/affirmative after any previous message - check if it's loan intent
        if msg.strip() in ["yes", "yeah", "yep", "sure", "ok", "okay", "yes please", "definitely"]:
            # Check if previous message was about loan/offers
            if len(state.get('messages', [])) > 0:
                last_ai = None
                for m in reversed(state['messages']):
                    if isinstance(m, AIMessage):
                        last_ai = (m.content or "").lower()
                        break
                
                if last_ai and ("apply" in last_ai or "loan" in last_ai or "offer" in last_ai):
                    return {
                        "messages": [AIMessage(content="Great! Let's get started. Please enter your **10-digit phone number** to proceed.")],
                        "step": "waiting_for_phone"
                    }

        # loan intent with amount
        amount = parse_loan_amount(msg_raw)
        if amount > 0 and any(w in msg for w in ["loan", "borrow", "need", "want", "apply"]):
            return {
                "messages": [AIMessage(content=f"I can help for ₹{amount}. To check eligibility, please enter your **10-digit phone number**.")],
                "loan_amount": amount,
                "step": "waiting_for_phone"
            }

        # Expanded loan intent detection - including wedding, medical, etc.
        loan_keywords = ["apply", "want a loan", "want loan", "need money", "need loan", 
                        "start", "borrow", "give me loan", "i need", "personal loan",
                        "wedding", "marriage", "medical", "education", "emergency"]
        if any(w in msg for w in loan_keywords):
            return {
                "messages": [AIMessage(content="Excellent! Let's get started with your loan application. 💼\n\nPlease share your **10-digit phone number** to proceed.")],
                "step": "waiting_for_phone"
            }

        # fallback LLM for small talk
        prompt = f"""
You are the Master Agent for Tata Capital.

PAST CONVERSATION:
{history_context}

INSTRUCTIONS:
- Answer user's latest message politely in 1-3 sentences.
- Use context to understand the user's intent.
- Mention offers if appropriate.
"""
        response = llm.invoke(prompt)
        text = getattr(response, "content", str(response))
        return {"messages": [AIMessage(content=text)], "step": "greet"}

    # -------- Final outcome routing (deterministic) --------
    if step == "final_outcome":
        decision = state.get("final_decision", {})
        if decision.get("status") == "APPROVED":
            pdf_path = create_sanction_letter(
                state['customer_name'],
                state['customer_phone'],
                state['loan_amount'],
                decision['new_emi'],
                12
            )
            link = f"http://127.0.0.1:8000/pdfs/{os.path.basename(pdf_path)}"
            final_msg = (
                f"🎉 **Sanction Letter Generated!**\n\n"
                f"✅ **Name:** {state['customer_name']}\n"
                f"✅ **Loan Amount:** ₹{state['loan_amount']}\n"
                f"✅ **Final EMI:** ₹{decision['new_emi']}\n\n"
                f"[Click to Download Final Slip]({link})"
            )
            return {"messages": [AIMessage(content=final_msg)], "step": "done"}

        if decision.get("status") == "NEEDS_DOCS":
            return {"messages": [AIMessage(content="⚠️ Request exceeds instant limit. Please upload **Salary Slip**.")], "step": "underwriting"}

        if decision.get("status") == "SOFT_REJECT":
            fallback = decision.get('fallback_offer')
            return {"messages": [AIMessage(content=f"We cannot approve the full amount. We can instantly approve **₹{fallback}**. Shall we proceed?")], "step": "sales"}

        return {"messages": [AIMessage(content=f"Application Rejected. Reason: {decision.get('reason','Not specified')}")], "step": "done"}

    # -------- waiting_for_phone helper --------
    if step == "waiting_for_phone":
        digits_only = re.sub(r"\D", "", msg)
        if len(digits_only) == 10:
            return {"step": "verifying"}
        elif len(digits_only) > 0:
            return {
                "messages": [AIMessage(content=f"I need exactly **10 digits**. You entered {len(digits_only)} digit{'s' if len(digits_only) != 1 else ''}. Please enter your complete phone number.")],
                "step": "waiting_for_phone"
            }
        return {"messages": [AIMessage(content="Please provide a valid 10-digit phone number.")], "step": "waiting_for_phone"}

    # treat worker-steps as nodes (no fallback LLM)
    if step in ['verifying', 'get_name', 'get_city', 'get_loan_purpose', 'sales', 'confirm_deal', 'underwriting']:
        return {"step": step}

    # -------- LLM fallback controller (rare) --------
    fallback_prompt = f"""
You are the Master Loan Agent for a bank. You are given the full conversation history below.

Conversation history:
{history_context}

Rules (must follow):
1) If you can answer the user without calling any backend tool, return a JSON object:
   {{ "assistant_reply": "<message to user>", "tool": null, "tool_args": null, "next_step": "greet|sales|confirm_deal|waiting_for_phone|underwriting|final_outcome|done" }}

2) If you need the backend to do something (verify phone, register user, run underwriting, or create a PDF),
   return a JSON object like:
   {{ "assistant_reply": "<message to the user (short)>",
      "tool": "verify"|"register"|"underwrite"|"create_pdf",
      "tool_args": {{... appropriate args ...}},
      "next_step": "verifying"|"sales"|"underwriting"|"final_outcome" }}
   - tool_args should include phone, amount, name as needed.

3) Only include plain text in assistant_reply. Do not output anything else.
4) If you cannot confidently decide, set tool=null and assistant_reply to a clarifying question.

Return ONLY valid JSON.
"""
    try:
        response = llm.invoke(fallback_prompt)
        llm_text = getattr(response, "content", str(response)).strip()
        parsed = json.loads(llm_text)

        # Defensive: ensure assistant_reply is string
        assistant_reply = str(parsed.get("assistant_reply", ""))  
        tool = parsed.get("tool")
        tool_args = parsed.get("tool_args") or {}
        next_step = parsed.get("next_step", state.get("step", "greet"))

        tool_result = None

        # ---- VERIFY TOOL ----
        if tool == "verify":
            phone = str(tool_args.get("phone") or state.get("customer_phone") or "")
            tool_result = verification_agent(phone)
            if tool_result.get("status") == "VERIFIED":
                assistant_reply += (
                    f"\n\n✅ Verification succeeded for {tool_result.get('name')}."
                    f" Pre-approved: ₹{tool_result.get('limit')}."
                )
                next_step = "sales"
            else:
                assistant_reply += "\n\nℹ️ Verification failed."
                next_step = "get_name"

        # ---- REGISTER TOOL ----
        elif tool == "register":
            phone = str(tool_args.get("phone") or state.get("customer_phone") or "")
            name = tool_args.get("name") or tool_args.get("customer_name") or state.get("customer_name")
            city = tool_args.get("city", "Unknown")
            res = register_agent(phone, name, city)
            tool_result = res
            assistant_reply += f"\n\n✅ Registered {res.get('name')} with limit ₹{res.get('limit')}."
            next_step = "sales"

        # ---- UNDERWRITE TOOL ----
        elif tool == "underwrite":
            phone = str(tool_args.get("phone") or state.get("customer_phone") or "")
            amount = int(tool_args.get("amount") or state.get("loan_amount") or 0)
            # prefer explicit tenure from tool_args, otherwise state default (12)
            tenure = int(tool_args.get("tenure") or state.get("loan_tenure", 12))
            uploaded = bool(tool_args.get("salary_slip_uploaded", False) or check_salary_slip_exists(phone))
            decision = underwriting_agent(phone, amount, salary_slip_uploaded=uploaded, tenure_months=tenure)
            tool_result = decision

            if decision.get("status") == "APPROVED":
                assistant_reply += f"\n\n✅ Approved. EMI: ₹{decision.get('new_emi')}"
                next_step = "final_outcome"
            elif decision.get("status") == "NEEDS_DOCS":
                assistant_reply += "\n\n⚠️ Income proof required. Please upload salary slip."
                next_step = "underwriting"
            elif decision.get("status") == "SOFT_REJECT":
                assistant_reply += f"\n\nWe can offer ₹{decision.get('fallback_offer')} instantly."
                next_step = "sales"
            else:
                assistant_reply += f"\n\nRejected. Reason: {decision.get('reason', 'N/A')}"
                next_step = "done"

        # ---- CREATE PDF TOOL ----
        elif tool == "create_pdf":
            phone = str(tool_args.get("phone") or state.get("customer_phone") or "")
            name = tool_args.get("name") or state.get("customer_name")
            amount = int(tool_args.get("amount") or state.get("loan_amount") or 0)
            emi = tool_args.get("emi") or calculate_emi(amount, 14, state.get("loan_tenure", 12))
            pdf_path = create_sanction_letter(name, phone, amount, emi, 12)
            link = f"http://127.0.0.1:8000/pdfs/{os.path.basename(pdf_path)}"
            assistant_reply += f"\n\nSanction letter ready: {link}"
            next_step = "done"

        # package AI response into result state
        ai_msg = AIMessage(content=assistant_reply)
        result_state = {"messages": [ai_msg], "step": next_step}

        # attach tool results where relevant
        if tool == "underwrite" and tool_result:
            result_state["final_decision"] = tool_result

        if tool in ("verify", "register") and tool_result and isinstance(tool_result, dict):
            if tool_result.get("name"):
                result_state["customer_name"] = (tool_args.get("name") or tool_result.get("name") or state.get("customer_name"))
            if tool_args.get("phone"):
                result_state["customer_phone"] = str(tool_args.get("phone"))

        if tool_args.get("amount") is not None:
            try:
                result_state["loan_amount"] = int(tool_args.get("amount"))
            except:
                result_state["loan_amount"] = state.get("loan_amount", 0)

        return result_state

    except Exception as e:
        # If LLM fallback failed, show its raw output (defensive)
        try:
            raw_text = getattr(response, "content", str(response))
        except Exception:
            raw_text = str(e)
        print("LLM fallback error:", e)
        return {"messages": [AIMessage(content=str(raw_text))], "step": "greet"}

# ==========================================================
# ===============  WORKER NODES (Enhanced with KYC) ========
# ==========================================================

def verification_node(state:AgentState):
    # Extract exactly 10 digits
    phone_match = re.findall(r"\d{10}", state['messages'][-1].content)
    if not phone_match:
        # Fallback: extract all digits and validate
        digits = re.sub(r"\D", "", state['messages'][-1].content)
        if len(digits) != 10:
            return {
                "messages": [AIMessage(content=f"I need exactly 10 digits for your phone number. You provided {len(digits)}. Please enter a valid 10-digit phone number.")],
                "step": "waiting_for_phone"
            }
        phone = digits
    else:
        phone = phone_match[0]
    
    r=verification_agent(phone)

    if r["status"]=="VERIFIED":
        # Include address verification for KYC compliance
        address = r.get('address', 'Address not on file')
        
        # Add structured tag for frontend card rendering
        loan_offer_tag = create_loan_offer_card(
            pre_approved_limit=r['limit'],
            interest_rate=INTEREST_RATE,
            max_tenure=60
        )
        
        msg = (
            f"{loan_offer_tag}\n"
            f"✅ **KYC Verification Successful!**\n\n"
            f"👤 **Name:** {r['name']}\n"
            f"📍 **Address on file:** {address}\n"
            f"💳 **Credit Score:** {r.get('credit_score', 'N/A')}\n"
            f"🏦 **Pre-approved Limit:** ₹{r['limit']:,}\n\n"
            f"Congratulations! You're pre-approved for a personal loan!\n\n"
            f"Is your address correct? If yes, please tell me:\n"
            f"1. **How much loan** do you need?\n"
            f"2. **What is the purpose?** (e.g., Wedding, Medical, Travel, Home Renovation, Education)"
        )
        return {
            "messages": [AIMessage(content=msg)],
            "customer_phone": phone,
            "customer_name": r['name'],
            "customer_address": address,
            "step": "get_loan_purpose"
        }

    return{"messages":[AIMessage(content="You seem new. What is your **Full Name**?")],"customer_phone":phone,"step":"get_name"}


def registration_name_node(state):
    raw = state['messages'][-1].content.strip()
    # print(raw)
    # If user accidentally sent an amount / phone / other noise, ask again politely
    if _looks_like_amount_or_noise(raw):
        return {
            "messages": [
                AIMessage(content=(
                    "Hm — that looks like an amount or some other info. "
                    "Could you please tell me your **Full Name** (e.g., Amit Sharma)?"
                ))
            ],
            "step": "get_name"
        }

    # If it doesn't look like a reasonable name, re-ask politely
    if not _is_probable_name(raw):
        return {
            "messages": [
                AIMessage(content="I didn't get that as your name. Please enter your **Full Name** (first and last name is helpful).")
            ],
            "step": "get_name"
        }

    name = raw
    return {
        "messages": [AIMessage(content=f"Great! Nice to meet you **{name}** 😊\nWhich city do you live in?")],
        "customer_name": name,
        "step": "get_city"
    }


def registration_city_node(state):
    city_raw = state['messages'][-1].content.strip()
    phone = state.get("customer_phone")
    name = state.get("customer_name")

    # If name is missing -> ask for it (DO NOT try to recover from history)
    # The registration_name_node only sets customer_name when name is valid,
    # so if it's missing here, the user never provided a valid name
    if not name:
        return {
            "messages": [AIMessage(content="I need your name first. Please tell me your **Full Name** (e.g., Amit Sharma).")],
            "step": "get_name"
        }

    # Validate city input
    if _looks_like_amount_or_noise(city_raw) or not _is_probable_city(city_raw):
        return {
            "messages": [AIMessage(content="That doesn't look like a city name. Which **city** do you live in? (e.g., Mumbai, Pune)")],
            "customer_name": name,
            "step": "get_city"
        }

    city = city_raw

    # Create customer now that we have name & city (phone may be None)
    r = register_agent(phone, name, city)

    # Add structured tag for frontend card rendering
    loan_offer_tag = create_loan_offer_card(
        pre_approved_limit=r['limit'],
        interest_rate=INTEREST_RATE,
        max_tenure=60
    )

    msg = (
        f"{loan_offer_tag}\n"
        f"🎉 **Registration Complete!**\n\n"
        f"👤 **Name:** {r['name']}\n"
        f"📍 **Address:** {r['address']}\n"
        f"🏦 **Pre-approved Limit:** ₹{r['limit']:,}\n"
        f"💳 **Credit Score:** {r['credit_score']}\n\n"
        f"Congratulations! You're pre-approved for a personal loan!\n\n"
        f"Now, please tell me:\n"
        f"1. **How much loan** do you need?\n"
        f"2. **What is the purpose?** (e.g., Wedding, Medical, Travel, Home Renovation, Education)"
    )

    return {
        "messages": [AIMessage(content=msg)],
        "customer_phone": phone,
        "customer_name": r["name"],
        "customer_address": r["address"],
        "step": "get_loan_purpose"
    }


def sales_node(state):
    msg=state['messages'][-1].content
    amt=parse_loan_amount(msg)

    if amt==0: return{"messages":[AIMessage(content="Enter loan amount (ex: 2 lakh, 50000)")],"step":"sales"}

    
    tenure = state.get('loan_tenure', 12)

    emi=calculate_emi(amt, INTEREST_RATE, tenure)
    purpose = state.get('loan_purpose', '')
    
    # Add structured tag for frontend card rendering
    loan_summary_tag = create_loan_summary_card(
        amount=amt,
        interest_rate=INTEREST_RATE,
        tenure=tenure,
        emi=emi
    )
    
    # Personalized message based on loan purpose
    purpose_msg = ""
    if purpose:
        purpose_msg = f"\n💡 For your **{purpose}** needs, this is a great choice!"
    
    return{
        "messages":[AIMessage(content=(
            f"{loan_summary_tag}\n"
            f"💰 **Loan Summary**\n\n"
            f"📊 **Amount:** ₹{amt:,}\n"
            f"📈 **Interest Rate:** {INTEREST_RATE}% p.a.\n"
            f"📅 **Tenure:** {tenure} months\n"
            f"💵 **Est. EMI:** ₹{emi:,.2f}/month"
            f"{purpose_msg}\n\n"
            f"✅ Ready to proceed? (yes/no)"
        ))],
        "loan_amount":amt,"step":"confirm_deal"
    }


def confirmation_node(state):
    m=state['messages'][-1].content.lower()
    if "yes" in m:return{"step":"underwriting"}
    if "no" in m:return{"messages":[AIMessage(content="Enter new amount.")],"step":"sales"}
    return{"messages":[AIMessage(content="Reply **yes** to continue.")],"step":"confirm_deal"}


def underwriting_node(state: AgentState):
    phone = state["customer_phone"]
    amt = state["loan_amount"]
    tenure = state.get("loan_tenure", 12)

    # 0️⃣ Safety check: If amount is missing, ask for it
    if not amt or amt <= 0:
        return {
            "messages": [
                AIMessage(
                    content="I need to know the **loan amount** you require before I can process your application. How much do you need?"
                )
            ],
            "step": "sales"  # Redirect to sales to capture amount
        }

    # 0.5️⃣ Safety check: If phone is missing (rare state loss), ask for it
    if not phone:
        return {
            "messages": [AIMessage(content="Could you please confirm your **10-digit phone number** again?")],
            "step": "waiting_for_phone"
        }

    # last user message text (explicit "uploaded" only)
    last_msg = ""
    if state.get("messages"):
        last_msg = state["messages"][-1].content or ""

    ui_text = last_msg.strip().lower()
    uploaded = ui_text in {"uploaded", "i uploaded", "file uploaded", "done upload"}



    # Call core underwriting logic
    decision = underwriting_agent(
        phone,
        amt,
        salary_slip_uploaded=uploaded,
        tenure_months=tenure,
    )

    status = decision.get("status")

    # 1️⃣ Docs required – just ask for slip and stop
    if status == "NEEDS_DOCS":
        return {
            "messages": [
                AIMessage(
                    content=(
                        "Amount above instant limit ⚠️ Please upload your **salary slip** to continue.\n\n"
                        "Once uploaded, just reply `uploaded` here and I’ll re-check your eligibility."
                    )
                )
            ],
            "final_decision": decision,
            "step": "underwriting",   # executor will treat this as 'unfinished'
        }
    
    customer_name = state.get("customer_name")
    if not customer_name:
        user = get_customer_by_phone(phone)
        if user:
            customer_name = user.get("name", "Customer")
        else:
            customer_name = "Customer"

    # 2️⃣ Approved – generate sanction letter here
    if status == "APPROVED":
        pdf_path = create_sanction_letter(
            customer_name,
            phone,
            amt,
            decision["new_emi"],
            tenure,
        )

        link = f"http://127.0.0.1:8000/pdfs/{os.path.basename(pdf_path)}"
        
        # Add structured tag for frontend card rendering
        approval_tag = create_approval_card(
            name=customer_name,
            amount=amt,
            emi=decision['new_emi'],
            pdf_link=link
        )

        msg = (
            f"{approval_tag}\n"
            f"🎉 **Loan Approved!**\n\n"
            f"✅ **Name:** {customer_name}\n"
            f"✅ **Loan Amount:** ₹{amt:,}\n"
            f"✅ **Final EMI:** ₹{decision['new_emi']:,.2f}\n\n"
            f"📄 [Click here to download your Sanction Letter]({link})"
        )

        return {
            "messages": [AIMessage(content=msg)],
            "final_decision": decision,
            "step": "done",
        }

    # 3️⃣ Soft reject – fallback offer with PERSUASIVE sales pitch
    if status == "SOFT_REJECT":
        fallback = decision.get("fallback_offer", 0)
        persuasion = decision.get("persuasion", "")
        fallback_emi = calculate_emi(fallback, INTEREST_RATE, tenure)
        
        # Add structured tag for frontend card rendering
        loan_summary_tag = create_loan_summary_card(
            amount=fallback,
            interest_rate=INTEREST_RATE,
            tenure=tenure,
            emi=fallback_emi
        )
        
        msg = (
            f"{loan_summary_tag}\n"
            f"I understand you were looking for ₹{amt:,}, but let me share some good news! 🌟\n\n"
            f"{persuasion}\n\n"
            f"📊 **Alternative Offer:**\n"
            f"💰 **Amount:** ₹{fallback:,}\n"
            f"💵 **EMI:** ₹{fallback_emi:,.2f}/month\n"
            f"📈 **Interest:** {INTEREST_RATE}% p.a.\n\n"
            f"This keeps your finances healthy while meeting your needs. "
            f"Would you like to proceed with ₹{fallback:,}? (yes/no)"
        )
        return {
            "messages": [AIMessage(content=msg)],
            "final_decision": decision,
            "loan_amount": fallback,  # Update to fallback amount
            "step": "confirm_deal",  # Go to confirmation, not sales
        }

    # 4️⃣ Hard reject – show reason and finish
    reason = decision.get("reason", "Not specified")
    
    # Add structured tag for frontend card rendering
    user = get_customer_by_phone(phone)
    credit_score = user.get('credit_score') if user else None
    rejection_tag = create_rejection_card(reason=reason, credit_score=credit_score)
    
    msg = f"{rejection_tag}\n❌ **Application Rejected**\n\nReason: {reason}"
    return {
        "messages": [AIMessage(content=msg)],
        "final_decision": decision,
        "step": "done",
    }


# ==========================================================
# ===============  LOAN PURPOSE NODE (Needs Analysis) ======
# ==========================================================

VALID_PURPOSES = {
    "wedding", "marriage", "medical", "health", "hospital", "treatment",
    "travel", "vacation", "holiday", "trip", "education", "study", "college",
    "home", "renovation", "repair", "house", "furniture", "appliance",
    "business", "startup", "investment", "car", "vehicle", "bike",
    "debt", "consolidation", "emergency", "personal", "other"
}

def _extract_purpose(text: str) -> str:
    """Extract loan purpose from user message."""
    text_lower = text.lower()
    for purpose in VALID_PURPOSES:
        if purpose in text_lower:
            # Return a clean version
            purpose_map = {
                "wedding": "Wedding", "marriage": "Wedding",
                "medical": "Medical Expenses", "health": "Medical Expenses", 
                "hospital": "Medical Expenses", "treatment": "Medical Expenses",
                "travel": "Travel", "vacation": "Travel", "holiday": "Travel", "trip": "Travel",
                "education": "Education", "study": "Education", "college": "Education",
                "home": "Home Improvement", "renovation": "Home Improvement", 
                "repair": "Home Improvement", "house": "Home Improvement",
                "furniture": "Home Improvement", "appliance": "Home Improvement",
                "business": "Business", "startup": "Business", "investment": "Business",
                "car": "Vehicle Purchase", "vehicle": "Vehicle Purchase", "bike": "Vehicle Purchase",
                "debt": "Debt Consolidation", "consolidation": "Debt Consolidation",
                "emergency": "Emergency", "personal": "Personal", "other": "Personal"
            }
            return purpose_map.get(purpose, purpose.title())
    return ""


def loan_purpose_node(state: AgentState):
    """
    Capture loan amount and purpose together for needs analysis.
    Makes the conversation more human-like by understanding WHY the customer needs the loan.
    """
    msg = state['messages'][-1].content
    
    # Try to extract both amount and purpose
    amt = parse_loan_amount(msg)
    purpose = _extract_purpose(msg)
    
    # If we got amount but no purpose, ask for purpose
    if amt > 0 and not purpose:
        return {
            "messages": [AIMessage(content=(
                f"Got it! You need **₹{amt:,}**. 💰\n\n"
                f"To help you better, what do you need this loan for?\n"
                f"(e.g., Wedding, Medical, Travel, Home Renovation, Education, Business)"
            ))],
            "loan_amount": amt,
            "step": "get_loan_purpose"
        }
    
    # If we got purpose but no amount, ask for amount
    if purpose and amt == 0:
        return {
            "messages": [AIMessage(content=(
                f"I see you need funds for **{purpose}**! That's a great reason. 🎯\n\n"
                f"How much loan amount do you need?"
            ))],
            "loan_purpose": purpose,
            "step": "get_loan_purpose"
        }
    
    # If we have both, proceed to sales with personalized message
    if amt > 0 and purpose:
        emi = calculate_emi(amt, INTEREST_RATE, 12)
        
        # Add structured tag for frontend card rendering
        loan_summary_tag = create_loan_summary_card(
            amount=amt,
            interest_rate=INTEREST_RATE,
            tenure=12,
            emi=emi
        )
        
        return {
            "messages": [AIMessage(content=(
                f"{loan_summary_tag}\n"
                f"Perfect! For your **{purpose}** needs, here's what I can offer:\n\n"
                f"💰 **Loan Summary**\n"
                f"📊 **Amount:** ₹{amt:,}\n"
                f"📈 **Interest Rate:** {INTEREST_RATE}% p.a.\n"
                f"📅 **Tenure:** 12 months\n"
                f"💵 **Est. EMI:** ₹{emi:,.2f}/month\n\n"
                f"✅ Ready to proceed? (yes/no)"
            ))],
            "loan_amount": amt,
            "loan_purpose": purpose,
            "step": "confirm_deal"
        }
    
    # Neither - ask for both
    return {
        "messages": [AIMessage(content=(
            "Please share:\n"
            "1. **Loan amount** you need (e.g., 2 lakh, 50000)\n"
            "2. **Purpose** of the loan (e.g., Wedding, Medical, Travel)"
        ))],
        "step": "get_loan_purpose"
    }


# ==========================================================
# ================ BUILD FLOW GRAPH ========================
# ==========================================================

workflow=StateGraph(AgentState)
workflow.add_node("router",master_node)
workflow.add_node("verifier",verification_node)
workflow.add_node("register_name",registration_name_node)
workflow.add_node("register_city",registration_city_node)
workflow.add_node("loan_purpose", loan_purpose_node)  # New node for needs analysis
workflow.add_node("sales",sales_node)
workflow.add_node("confirmer",confirmation_node)
workflow.add_node("underwriter",underwriting_node)

workflow.set_entry_point("router")

def route(state):
    s=state['step']
    if s in["greet","waiting_for_phone","done"]: return "stop"
    return s

workflow.add_conditional_edges(
    "router",route,{
        "verifying":"verifier",
        "get_name":"register_name",
        "get_city":"register_city",
        "get_loan_purpose": "loan_purpose",  # New route for loan purpose
        "sales":"sales",
        "confirm_deal":"confirmer",
        "underwriting":"underwriter",
        "final_outcome":"router",
        "stop":END
    }
)

workflow.add_edge("verifier", END)
workflow.add_edge("register_name", END)
workflow.add_edge("register_city", END)
workflow.add_edge("loan_purpose", END)  # New edge
workflow.add_edge("sales", END)
workflow.add_edge("confirmer", "router")
workflow.add_edge("underwriter", END)

app_graph=workflow.compile()


# ==========================================================
# EXECUTOR WORKS SAME — no change required
# ==========================================================

class GraphExecutor:
    def invoke(self, input_dict):
        """
        input_dict keys:
          - input: str (user message)
          - chat_history: list[BaseMessage] (previous chat messages)
          - session_id: str  (session identifier)
          - tenure: int (optional)
        """
        user_input = (input_dict.get('input') or "").strip()
        hist = input_dict.get('chat_history') or []
        session_id = input_dict.get('session_id')

        # Keep last 50 messages for memory
        recent_hist = hist[-50:] if len(hist) > 50 else hist

        # helper to join content
        def full_text(messages):
            try:
                return " ".join([m.content for m in messages])
            except Exception:
                return " ".join([m.get("content") if isinstance(m, dict) else str(m) for m in messages])

        full = full_text(recent_hist)
        full_lower = full.lower()

        # ---------------- RECONSTRUCT STATE ----------------
        step = "greet"
        phone = None
        name = None
        city = None
        amt = 0

        from langchain_core.messages import AIMessage, HumanMessage

        last_ai_prompt = None
        last_ai_text = ""

        # Walk messages in order and infer state
        for m in recent_hist:
            if isinstance(m, AIMessage):
                last_ai_prompt = (m.content or "").lower()
                last_ai_text = m.content or ""

                # Check if loan was completed (sanction letter generated)
                if ("sanction letter" in last_ai_prompt and "download" in last_ai_prompt) or \
                   ("congratulations" in last_ai_prompt and "approved" in last_ai_prompt) or \
                   "[approval]" in last_ai_prompt or \
                   "application rejected" in last_ai_prompt or \
                   "[rejection]" in last_ai_prompt:
                    step = "done"

                # Extract name from "Nice to meet you **{name}**" pattern
                name_match = re.search(r"nice to meet you \*?\*?([^*\n😊]+)", last_ai_prompt)
                if name_match:
                    extracted_name = name_match.group(1).strip()
                    if extracted_name and len(extracted_name) > 1:
                        name = extracted_name
                
                # Also extract from registration complete messages
                name_match2 = re.search(r"\*?\*?name:\*?\*?\s*([^\n*]+)", last_ai_prompt)
                if name_match2:
                    extracted_name = name_match2.group(1).strip()
                    if extracted_name and len(extracted_name) > 1:
                        name = extracted_name

                # Check for structured tags first to extract amount reliably
                summary_match = re.search(r"\[LOAN_SUMMARY\](.*?)\[/LOAN_SUMMARY\]", m.content, re.DOTALL)
                if summary_match:
                    step = "confirm_deal"
                    try:
                        data = json.loads(summary_match.group(1))
                        if "amount" in data:
                            amt = int(data["amount"])
                    except:
                        pass
                
                # Fallback to text regex if no tag or tag parsing failed
                elif "loan summary" in last_ai_prompt or "est. emi" in last_ai_prompt:
                    step = "confirm_deal"
                    m_amount = re.search(r"amount[:\*\s]*₹\s*([0-9,]+)", m.content, flags=re.IGNORECASE)
                    if m_amount:
                        try:
                            amt = int(m_amount.group(1).replace(",", ""))
                        except Exception:
                            pass

                # Verification/registration completed → sales
                if ("verification successful" in last_ai_prompt
                        or "verified " in last_ai_prompt
                        or "registration successful" in last_ai_prompt
                        or "registration complete" in last_ai_prompt):
                    step = "sales"

                # Ask name / city → corresponding step
                if "what is your full name" in last_ai_prompt or "you seem new" in last_ai_prompt:
                    step = "get_name"
                if "which city" in last_ai_prompt or "which city do you live" in last_ai_prompt:
                    step = "get_city"

                continue

            if isinstance(m, HumanMessage):
                txt = (m.content or "").strip()
                txt_l = txt.lower()

                # If last AI asked for name, capture this message as name
                if last_ai_prompt and ("what is your full name" in last_ai_prompt or "you seem new" in last_ai_prompt or "full name" in last_ai_prompt):
                    if _is_probable_name(txt):
                        name = txt

                # capture phone if user typed it anywhere
                digits = re.findall(r"\d{10,}", txt)
                if digits:
                    phone = digits[-1][-10:]

                # If last AI prompt was loan summary, user might be modifying amount
                if last_ai_prompt and ("loan summary" in last_ai_prompt or "emi" in last_ai_prompt):
                    try:
                        parsed_amt = parse_loan_amount(txt)
                    except Exception:
                        parsed_amt = 0
                    if parsed_amt and parsed_amt > 0:
                        amt = parsed_amt

                # user might give amount directly
                try:
                    parsed_amt = parse_loan_amount(txt)
                except Exception:
                    parsed_amt = 0
                if parsed_amt and parsed_amt > 0:
                    amt = parsed_amt
                    if step == "greet":
                        step = "waiting_for_phone"

        # Fallback heuristics
        if step == "greet":
            if "loan summary" in full_lower or "est. emi" in full_lower:
                step = "confirm_deal"
            elif ("verification successful" in full_lower or "verified " in full_lower
                  or "registration successful" in full_lower or "registration complete" in full_lower
                  or "kyc verification successful" in full_lower):
                step = "get_loan_purpose"  # Go to loan purpose after verification
            elif "what is the purpose" in full_lower or "what do you need this loan for" in full_lower:
                step = "get_loan_purpose"
            elif "which city" in full_lower:
                step = "get_city"
            elif "what is your full name" in full_lower or "full name" in full_lower:
                step = "get_name"

        if (
            step == "underwriting"
            and any(p in ui_lc for p in ["uploaded", "i uploaded", "file uploaded"])
        ):
            step = "underwriting"


        # Extract phone from full history if still None
        if phone is None:
            digits_all = re.findall(r"\d{10,}", full)
            if digits_all:
                phone = digits_all[-1][-10:]

        last_ai_snippet = (last_ai_text[:80] if last_ai_text
                           else (recent_hist[-1].content[:80] if recent_hist else ""))
        print(f"--- EXECUTOR: inferred step='{step}' | amt={amt} | phone={phone} | "
              f"name={name} | last_ai='{last_ai_snippet}'")

        # ---------------- RESUME / START-NEW LOGIC ----------------
        ui_lc = user_input.lower().strip()

        # If loan was completed (step is done), reset to greet for new conversation
        if step == "done":
            # User wants to start a fresh conversation after loan completion
            initial_state = {
                "messages": [HumanMessage(content=user_input)],
                "step": "greet",
                "customer_phone": None,
                "customer_name": None,
                "loan_amount": 0,
                "loan_tenure": input_dict.get("tenure", 12),
                "offered_discount": False,
                "final_decision": {}
            }
            result = app_graph.invoke(initial_state)
            if not result.get('messages'):
                return {"output": "System Error: No response generated."}
            return {"output": result['messages'][-1].content}

        unfinished_steps = {
            "confirm_deal",
            "underwriting",
            "sales",
            "waiting_for_phone",
            "get_name",
            "get_city",
            "get_loan_purpose",  # Added for loan purpose flow
        }
        is_unfinished = step in unfinished_steps

        simple_greetings = {"hi", "hey", "hello", "hey there"}

        # 1️⃣ User says hi/hello while there is an unfinished flow
        if ui_lc in simple_greetings and is_unfinished:
            return {
                "output": (
                    "It looks like you were in the middle of a loan application earlier. "
                    "Reply **resume** to continue from where you stopped or **start new** to begin again."
                )
            }

        # 2️⃣ User explicitly says resume
        if ui_lc in {"resume", "continue", "yes resume", "resume please", "continue please"} and is_unfinished:

            # 🔁 If we were in registration (name or city), restart from NAME fresh
            if step in {"get_name", "get_city"}:
                return {
                    "output": (
                        "No problem, let's restart your registration 😊\n"
                        "Please tell me your **Full Name**."
                    )
                }

            # For other steps (sales, confirm_deal, underwriting, etc.) → continue flow
            # IMPORTANT: do NOT append 'resume' message into the graph state
            initial_state = {
                "messages": recent_hist,
                "step": step,
                "customer_phone": phone,
                "customer_name": name,
                "loan_amount": amt,
                "loan_tenure": input_dict.get("tenure", 12),
                "offered_discount": False,
                "final_decision": {}
            }
            result = app_graph.invoke(initial_state)
            if not result.get('messages'):
                return {"output": "System Error: No response generated."}
            return {"output": result['messages'][-1].content}

        # 3️⃣ User says start new
        if ui_lc in {"start new", "new", "start over", "reset session"}:
            registered = (
                "registration complete" in full_lower
                or "registration successful" in full_lower
                or "verification successful" in full_lower
                or "verified " in full_lower
            )
            if registered:
                initial_state = {
                    "messages": recent_hist + [HumanMessage(content=user_input)],
                    "step": "sales",
                    "customer_phone": phone,
                    "customer_name": name,
                    "loan_amount": 0,
                    "loan_tenure": input_dict.get("tenure", 12),
                    "offered_discount": False,
                    "final_decision": {}
                }
            else:
                initial_state = {
                    "messages": recent_hist + [HumanMessage(content=user_input)],
                    "step": "greet",
                    "customer_phone": None,
                    "customer_name": None,
                    "loan_amount": 0,
                    "loan_tenure": input_dict.get("tenure", 12),
                    "offered_discount": False,
                    "final_decision": {}
                }
            result = app_graph.invoke(initial_state)
            if not result.get('messages'):
                return {"output": "System Error: No response generated."}
            return {"output": result['messages'][-1].content}

        # ---------------- NORMAL FLOW ----------------
        initial_state = {
            "messages": recent_hist + [HumanMessage(content=user_input)],
            "step": step,
            "customer_phone": phone,
            "customer_name": name,
            "loan_amount": amt,
            "loan_tenure": input_dict.get("tenure", 12),
            "offered_discount": False,
            "final_decision": {}
        }

        result = app_graph.invoke(initial_state)
        if not result.get('messages'):
            return {"output": "System Error: No response generated."}
        return {"output": result['messages'][-1].content}


agent_executor = GraphExecutor()
