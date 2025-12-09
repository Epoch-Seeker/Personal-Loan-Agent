# ===============================================
# master_agent.py  (Salary SYSTEM REMOVED)
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
    check_salary_slip_exists
)
from pdf_generator import create_sanction_letter
from mock_data import get_customer_by_phone

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
    loan_amount: int
    loan_tenure: int
    step: str
    offered_discount: bool
    final_decision: Optional[dict]

def get_history_string(messages, limit=50):
    s=""
    for m in messages[-limit:]:
        role="User" if isinstance(m,HumanMessage) else "AI"
        s+=f"{role}: {m.content}\n"
    return s

# add near other imports
_LOAN_KEYWORDS = {"lakh", "lac", "loan", "rupee", "rupees", "k", "thousand", "amount", "emi"}

def _looks_like_amount_or_noise(text: str) -> bool:
    t = text.lower()
    if any(ch.isdigit() for ch in t):
        return True
    for kw in _LOAN_KEYWORDS:
        if kw in t:
            return True
    return False

def _is_probable_name(text: str) -> bool:
    """Check if given input looks like a real person's name."""
    if not text:
        return False

    raw = text.strip()
    low = raw.lower()

    # Reject greetings / commands / resume related words
    bad_tokens = {"hi", "hii", "hey", "hello", "yo", "ok", "k", "resume", "start new"}
    if low in bad_tokens:
        return False

    # Reject too small / too large
    if len(raw) < 2 or len(raw) > 60:
        return False

    # No digits allowed
    if any(ch.isdigit() for ch in raw):
        return False

    # Reject loan or money related input accidentally typed here
    loan_keywords = {"loan", "emi", "amount", "borrow", "rs", "rupee", "₹", "salary", "limit"}
    if any(kw in low for kw in loan_keywords):
        return False

    # Must contain alphabet characters only (spaces allowed)
    if not re.fullmatch(r"[a-zA-Z\s]{2,60}", raw):
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
        prompt = f"""You are the Master Agent. Short summary of CURRENT OFFERS only:
CONVERSATION HISTORY:
{history_context}

OFFERS:
{offers}

Provide a short summary the user would understand, in one or two lines."""
        response = llm.invoke(prompt)
        text = getattr(response, "content", str(response))
        return {"messages": [AIMessage(content=text)], "step": "greet"}

    # -------- Phase: greet (deterministic intent checks) --------
    if step == "greet":
        # phone typed directly -> verify
        if any(char.isdigit() for char in msg) and len(re.sub(r"\D", "", msg)) >= 10:
            return {"step": "verifying"}

        # greeting small talk
        greetings = ["hi", "hello", "hey", "greetings"]
        if any(msg.strip().startswith(g) for g in greetings) and len(msg) < 20:
            return {
                "messages": [AIMessage(content="Hello! Welcome to Tata Capital. I can help with personal loans — would you like to check offers or apply now?")],
                "step": "greet"
            }

        # loan intent with amount
        amount = parse_loan_amount(msg_raw)
        if amount > 0 and any(w in msg for w in ["loan", "borrow", "need", "want", "apply"]):
            return {
                "messages": [AIMessage(content=f"I can help for ₹{amount}. To check eligibility, please enter your **10-digit phone number**.")],
                "loan_amount": amount,
                "step": "waiting_for_phone"
            }

        # simple loan intent without amount
        if any(w in msg for w in ["apply", "want a loan", "need money", "start", "borrow"]):
            return {
                "messages": [AIMessage(content="Excellent — let's get started. Please enter your registered **Phone Number**.")],
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
        if any(char.isdigit() for char in msg) and len(re.sub(r"\D", "", msg)) >= 10:
            return {"step": "verifying"}
        return {"messages": [AIMessage(content="Please provide a valid 10-digit phone number.")], "step": "waiting_for_phone"}

    # treat worker-steps as nodes (no fallback LLM)
    if step in ['verifying', 'get_name', 'get_city', 'sales', 'confirm_deal', 'underwriting']:
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
# ===============  WORKER NODES (salary removed) ===========
# ==========================================================

def verification_node(state:AgentState):
    phone=re.findall(r"\d{10}",state['messages'][-1].content)[0]
    r=verification_agent(phone)

    if r["status"]=="VERIFIED":
        msg=f"✅ Verified {r['name']}.\nPre-approved limit: ₹{r['limit']}\n\nLoan amount?"
        return{"messages":[AIMessage(content=msg)],"customer_phone":phone,"customer_name":r['name'],"step":"sales"}

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

    # If name is missing in state, try to recover from history (best-effort)
    if not name:
        for i, m in enumerate(state.get("messages", [])):
            txt = getattr(m, "content", "")
            # find the human message immediately after "Full Name" prompt
            if "full name" in txt.lower() and i + 1 < len(state["messages"]):
                cand = state["messages"][i + 1].content.strip()
                if _is_probable_name(cand):
                    name = cand
                    break

    # If name is still missing -> ask for it explicitly (do NOT store city as name)
    if not name:
        return {
            "messages": [AIMessage(content="I think I missed your name. Please tell me your **Full Name** first.")],
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

    msg = (
        f"🎉 Registration Complete!\n"
        f"Welcome **{r['name']}** from **{r['city']}**.\n"
        f"🏦 Pre-approved Limit: **₹{r['limit']}**\n\n"
        f"Now tell me how much **loan amount** you want."
    )

    return {
        "messages": [AIMessage(content=msg)],
        "customer_phone": phone,
        "customer_name": r["name"],
        "customer_city": r["city"],
        "step": "sales"
    }


def sales_node(state):
    msg=state['messages'][-1].content
    amt=parse_loan_amount(msg)

    if amt==0: return{"messages":[AIMessage(content="Enter loan amount (ex: 2 lakh, 50000)")],"step":"sales"}

    emi=calculate_emi(amt,14,12)
    return{
        "messages":[AIMessage(content=f"💰 Loan Summary\nAmount:₹{amt}\nEMI≈₹{emi}\nProceed? (yes/no)")],
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

    # last user message text (for "uploaded" etc.)
    last_msg = ""
    if state.get("messages"):
        last_msg = state["messages"][-1].content or ""

    uploaded = (
        check_salary_slip_exists(phone) or
        any(p in last_msg.lower() for p in ["uploaded", "i uploaded", "file uploaded", "done upload"])
    )

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

        pdf_path = create_sanction_letter(
            customer_name,
            phone,
            amt,
            decision["new_emi"],
            tenure,
        )

    # 2️⃣ Approved – generate sanction letter here
    if status == "APPROVED":

        link = f"http://127.0.0.1:8000/pdfs/{os.path.basename(pdf_path)}"

        msg = (
            f"🎉 **Loan Approved!**\n\n"
            f"✅ **Name:** {customer_name}\n"
            f"✅ **Loan Amount:** ₹{amt}\n"
            f"✅ **Final EMI:** ₹{decision['new_emi']}\n\n"
            f"📄 [Click here to download your Sanction Letter]({link})"
        )

        return {
            "messages": [AIMessage(content=msg)],
            "final_decision": decision,
            "step": "done",
        }

    # 3️⃣ Soft reject – fallback offer, go back to sales
    if status == "SOFT_REJECT":
        fallback = decision.get("fallback_offer", 0)
        msg = (
            f"Sorry, we can’t approve ₹{amt} right now.\n"
            f"However, we can instantly approve **₹{fallback}**.\n"
            f"Would you like to proceed with this amount?"
        )
        return {
            "messages": [AIMessage(content=msg)],
            "final_decision": decision,
            "step": "sales",
        }

    # 4️⃣ Hard reject – show reason and finish
    reason = decision.get("reason", "Not specified")
    msg = f"❌ Application Rejected. Reason: {reason}"
    return {
        "messages": [AIMessage(content=msg)],
        "final_decision": decision,
        "step": "done",
    }



# ==========================================================
# ================ BUILD FLOW GRAPH ========================
# ==========================================================

workflow=StateGraph(AgentState)
workflow.add_node("router",master_node)
workflow.add_node("verifier",verification_node)
workflow.add_node("register_name",registration_name_node)
workflow.add_node("register_city",registration_city_node)
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

                # Loan summary → confirm_deal
                if "loan summary" in last_ai_prompt or "est. emi" in last_ai_prompt:
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
                if "what is your full name" in last_ai_prompt or "full name" in last_ai_prompt:
                    step = "get_name"
                if "which city" in last_ai_prompt or "which city do you live" in last_ai_prompt:
                    step = "get_city"

                continue

            if isinstance(m, HumanMessage):
                txt = (m.content or "").strip()
                txt_l = txt.lower()

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
                  or "registration successful" in full_lower or "registration complete" in full_lower):
                step = "sales"
            elif "which city" in full_lower:
                step = "get_city"
            elif "what is your full name" in full_lower or "full name" in full_lower:
                step = "get_name"

        # Underwriting override
        if ("upload" in full_lower or "salary slip" in full_lower) and step != "confirm_deal":
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

        unfinished_steps = {
            "confirm_deal",
            "underwriting",
            "sales",
            "waiting_for_phone",
            "get_name",
            "get_city",
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
