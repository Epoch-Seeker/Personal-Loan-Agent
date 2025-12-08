# master_agent.py
import os
import re
import json
from typing import TypedDict, Annotated, Optional
import operator
from dotenv import load_dotenv

load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langgraph.graph import StateGraph, END

# Import Logic (workers)
from agents import (
    verification_agent,
    underwriting_agent,
    register_agent,
    fetch_general_offers,
    calculate_emi,
    parse_loan_amount,
    check_salary_slip_exists,
    parse_salary,
)
from pdf_generator import create_sanction_letter

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

# --- STATE DEFINITION ---
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    customer_phone: Optional[str]
    customer_name: Optional[str]
    loan_amount: int
    step: str 
    offered_discount: bool
    final_decision: Optional[dict]

# --- HELPER: FORMAT HISTORY FOR LLM ---
def get_history_string(messages, limit=50):
    """Combines last N messages into a string for the LLM context."""
    recent_msgs = messages[-limit:]
    history_str = ""
    for m in recent_msgs:
        role = "User" if isinstance(m, HumanMessage) else "AI"
        history_str += f"{role}: {m.content}\n"
    return history_str

# --- 1. MASTER AGENT ---
def master_node(state: AgentState):
    """
    Deterministic-first routing:
      - If an if/else condition matches, return its deterministic response.
      - Otherwise, send the entire session history + latest message to LLM.
        The LLM should produce JSON: {"assistant_reply": "...", "tool": "verify"|"register"|"underwrite"|"create_pdf"|None, "tool_args": {...}, "next_step": "..."}
      - Tools are executed in Python (so rules stay enforced).
    """
    # Ensure last message exists
    if not state.get('messages'):
        return {"messages": [AIMessage(content="Hello! How can I help you today?")], "step": "greet"}

    msg_raw = state['messages'][-1].content
    msg = msg_raw.lower()
    step = state.get('step', 'greet')
    history_context = get_history_string(state['messages'], limit=50)

    print(f"--- MASTER: Step '{step}' | User said: {msg[:60]} ---")

    # --- GLOBAL INTERRUPTS ---
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

    # QUICK: offers intent handled deterministically
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

    # --- PHASE 1: GREETING & INTENT --- (deterministic)
    if step == 'greet':
        # PHONE CHECK
        if any(char.isdigit() for char in msg) and len(re.sub(r"\D", "", msg)) >= 10:
            return {"step": "verifying"}

        greetings = ["hi", "hello", "hey", "greetings"]
        if any(msg.strip().startswith(g) for g in greetings) and len(msg) < 20:
            return {
                "messages": [AIMessage(content="Hello! Welcome to Tata Capital. I can help you with Personal Loans. Would you like to check offers or apply now?")],
                "step": "greet"
            }

        # LOAN INTENT (Amount Mentioned) - use robust parser
        amount = parse_loan_amount(msg_raw)
        if amount > 0 and any(w in msg for w in ["loan", "borrow", "need", "want", "apply"]):
            return {
                "messages": [AIMessage(content=f"I can certainly help with a loan of ₹{amount}. To check eligibility, please enter your **10-digit Phone Number**.")],
                "loan_amount": amount,
                "step": "waiting_for_phone"
            }

        # SIMPLE LOAN INTENT without amount
        if any(w in msg for w in ["apply", "want a loan", "need money", "start", "borrow"]):
            return {
                "messages": [AIMessage(content="Excellent! Let's get started. Please enter your registered **Phone Number**.")],
                "step": "waiting_for_phone"
            }

        # FALLBACK: let LLM handle casual chat (but still deterministic fallback)
        offers = fetch_general_offers()
        prompt = f"""
You are the Master Agent for Tata Capital.

PAST CONVERSATION:
{history_context}

INSTRUCTIONS:
- Answer user's latest message politely in 1-3 sentences.
- Use context to understand the user's intent.
- Mention offers if it's appropriate.
"""
        response = llm.invoke(prompt)
        text = getattr(response, "content", str(response))
        return {"messages": [AIMessage(content=text)], "step": "greet"}

    # --- PHASE 2: CLOSING & ROUTING (deterministic small checks) ---
    if step == 'final_outcome':
        decision = state.get('final_decision', {})
        if decision.get("status") == "APPROVED":
            pdf_path = create_sanction_letter(
                state['customer_name'],
                state['customer_phone'],
                state['loan_amount'],
                decision['new_emi'],
                12
            )
            link = f"http://127.0.0.1:8000/pdfs/{os.path.basename(pdf_path)}"
            final_msg = f"""🎉 **Sanction Letter Generated!**
\n✅ **Name:** {state['customer_name']}
\n✅ **Loan Amount:** ₹{state['loan_amount']}
\n✅ **Final EMI:** ₹{decision['new_emi']}
\n[Click to Download Final Slip]({link})"""
            return {"messages": [AIMessage(content=final_msg)], "step": "done"}

        elif decision.get("status") == "NEEDS_DOCS":
            return {
                "messages": [AIMessage(content="⚠️ Request exceeds instant limit. Please upload **Salary Slip**.")],
                "step": "underwriting"
            }

        elif decision.get("status") == "SOFT_REJECT":
            fallback = decision['fallback_offer']
            return {
                "messages": [AIMessage(
                    content=f"We cannot approve the full amount. However, we can instantly approve **₹{fallback}**. Shall we proceed?"
                )],
                "step": "sales"
            }

        else:
            return {
                "messages": [AIMessage(content=f"Application Rejected. Reason: {decision.get('reason', 'Not specified')}")],
                "step": "done"
            }

    # ROUTING helper: waiting_for_phone
    if step == "waiting_for_phone":
        if any(char.isdigit() for char in msg) and len(re.sub(r"\D", "", msg)) >= 10:
            return {"step": "verifying"}
        return {
            "messages": [AIMessage(content="Please provide a valid 10-digit phone number.")],
            "step": "waiting_for_phone"
        }

    # 🔴 IMPORTANT FIX: treat all worker-steps (including get_salary) as graph nodes,
    # so they do NOT go to LLM fallback.
    if step in ['verifying', 'get_name', 'get_city', 'get_salary', 'sales', 'confirm_deal', 'underwriting']:
        # Router will send control to the corresponding node (verifier / register_* / sales / confirmer / underwriter)
        return {"step": step}

    # --- If we reach here, none of the deterministic rules matched.
    # Use LLM as fallback controller. LLM will be given full history and must return JSON or plain reply.
    # We instruct the LLM to return either a JSON with {assistant_reply, tool, tool_args, next_step}
    # or plain text reply. Tool names supported: verify, register, underwrite, create_pdf, none.
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

Now analyze the conversation and produce the JSON described above.
"""
    try:
        response = llm.invoke(fallback_prompt)
        llm_text = getattr(response, "content", str(response)).strip()

        # Try parse JSON
        parsed = json.loads(llm_text)
        assistant_reply = parsed.get("assistant_reply", "")
        tool = parsed.get("tool")
        tool_args = parsed.get("tool_args") or {}
        next_step = parsed.get("next_step", state.get("step", "greet"))

        # Execute tool calls server-side if requested
        tool_result = None
        if tool == "verify":
            phone = tool_args.get("phone") or state.get("customer_phone")
            tool_result = verification_agent(phone)
            if tool_result.get("status") == "VERIFIED":
                assistant_reply = assistant_reply + (
                    f"\n\n✅ Verification succeeded for {tool_result.get('name')}."
                    f" Pre-approved: ₹{tool_result.get('limit')}."
                )
            else:
                assistant_reply = assistant_reply + "\n\nℹ️ Verification failed."
            next_step = "sales" if tool_result.get("status") == "VERIFIED" else "get_name"

        elif tool == "register":
            phone = tool_args.get("phone") or state.get("customer_phone")
            name = tool_args.get("name") or tool_args.get("customer_name") or state.get("customer_name")
            city = tool_args.get("city", "Unknown")
            res = register_agent(phone, name, city)
            tool_result = res
            assistant_reply = assistant_reply + f"\n\n✅ Registered {res.get('name')} with limit ₹{res.get('limit')}."
            next_step = "sales"

        elif tool == "underwrite":
            phone = tool_args.get("phone") or state.get("customer_phone")
            amount = tool_args.get("amount") or state.get("loan_amount")
            uploaded = tool_args.get("salary_slip_uploaded", False) or check_salary_slip_exists(phone)
            decision = underwriting_agent(phone, amount, salary_slip_uploaded=uploaded)
            tool_result = decision
            if decision.get("status") == "APPROVED":
                assistant_reply = assistant_reply + f"\n\n✅ Approved. EMI: ₹{decision.get('new_emi')}"
                next_step = "final_outcome"
            elif decision.get("status") == "NEEDS_DOCS":
                assistant_reply = assistant_reply + "\n\n⚠️ Income proof required. Please upload salary slip."
                next_step = "underwriting"
            elif decision.get("status") == "SOFT_REJECT":
                assistant_reply = assistant_reply + f"\n\nWe can offer ₹{decision.get('fallback_offer')} instantly."
                next_step = "sales"
            else:
                assistant_reply = assistant_reply + f"\n\nRejected. Reason: {decision.get('reason', 'N/A')}"
                next_step = "done"

        elif tool == "create_pdf":
            phone = tool_args.get("phone") or state.get("customer_phone")
            name = tool_args.get("name") or state.get("customer_name")
            amount = tool_args.get("amount") or state.get("loan_amount")
            emi = tool_args.get("emi") or calculate_emi(amount, 14, 12)
            pdf_path = create_sanction_letter(name, phone, amount, emi, 12)
            link = f"http://127.0.0.1:8000/pdfs/{os.path.basename(pdf_path)}"
            assistant_reply = assistant_reply + f"\n\nSanction letter ready: {link}"
            next_step = "done"

        ai_msg = AIMessage(content=assistant_reply)
        result_state = {"messages": [ai_msg], "step": next_step}

        if tool == "underwrite" and tool_result:
            result_state["final_decision"] = tool_result
        if tool in ("verify", "register") and tool_result and isinstance(tool_result, dict):
            if tool_result.get("name"):
                result_state["customer_name"] = (
                    tool_args.get("name") or tool_result.get("name") or state.get("customer_name")
                )
            if tool_args.get("phone"):
                result_state["customer_phone"] = tool_args.get("phone")

        if tool_args.get("amount"):
            result_state["loan_amount"] = tool_args.get("amount")

        return result_state

    except Exception as e:
        print("LLM fallback error:", e)
        raw_text = getattr(response, "content", str(response))
        return {"messages": [AIMessage(content=raw_text)], "step": "greet"}

# --- 2. WORKER AGENTS (unchanged) ---

def verification_node(state: AgentState):
    print("--- AGENT: Verification ---")
    last_msg = state['messages'][-1].content
    phone = "".join(filter(str.isdigit, last_msg))[-10:]
    result = verification_agent(phone)
    if result["status"] == "VERIFIED":
        msg = f"✅ **Verification Successful!**\nWelcome **{result['name']}**.\nYour Pre-approved Limit is ₹{result['limit']}."
        if state.get('loan_amount', 0) > 0:
            msg += f"\n\nI recall you requested **₹{state['loan_amount']}**. Shall I proceed?"
        else:
            msg += "\n\nHow much loan would you like to apply for?"
        return {
            "messages": [AIMessage(content=msg)],
            "customer_phone": phone,
            "customer_name": result['name'],
            "step": "sales"
        }
    else:
        return {
            "messages": [AIMessage(content="It looks like you are new to Tata Capital. Let's get you registered.\n\n**What is your Full Name?**")],
            "customer_phone": phone,
            "step": "get_name"
        }

def registration_name_node(state: AgentState):
    name = state['messages'][-1].content
    return {
        "messages": [AIMessage(content=f"Thanks {name}. **Which City do you live in?**")],
        "customer_name": name,
        "step": "get_city"
    }

def registration_city_node(state: AgentState):
    """Store city, then ask for monthly salary."""
    city = state['messages'][-1].content
    return {
        "messages": [AIMessage(content="Great. What is your **monthly salary** (in rupees)?")],
        "customer_city": city,
        "step": "get_salary",
    }

def registration_salary_node(state: AgentState):
    """Ask for monthly salary → register customer with computed score + limit"""
    salary_text = state['messages'][-1].content
    salary = parse_salary(salary_text)

    if salary <= 0:
        return {
            "messages": [AIMessage(
                content="Please enter a valid salary amount (e.g., 60k, 1.5 lakh, 75000)."
            )],
            "step": "get_salary"
        }

    # 1️⃣ Get from state first
    phone = state.get('customer_phone')
    name = state.get('customer_name')
    city = state.get('customer_city')

    # 2️⃣ If anything missing, try to recover from history
    msgs = state["messages"]
    for i, m in enumerate(msgs):
        text = getattr(m, "content", str(m)).lower()

        # Name: user message right after "What is your Full Name?"
        if "what is your full name" in text and i + 1 < len(msgs) and not name:
            next_msg = msgs[i + 1]
            if isinstance(next_msg, HumanMessage):
                name = next_msg.content.strip()

        # City: user message right after "Which City do you live in?"
        if "which city do you live in" in text and i + 1 < len(msgs) and not city:
            next_msg = msgs[i + 1]
            if isinstance(next_msg, HumanMessage):
                city = next_msg.content.strip()

        # Phone: any 10-digit number we’ve seen
        digits = re.findall(r"\d{10,}", text)
        if digits and not phone:
            phone = digits[-1][-10:]

    # 3️⃣ If still missing, push user back to the right step instead of saving bad data
    if not name:
        return {
            "messages": [AIMessage(content="I didn’t catch your name earlier. Please tell me your **Full Name**.")],
            "step": "get_name"
        }

    if not city:
        return {
            "messages": [AIMessage(content=f"Thanks {name}. Which **City** do you live in?")],
            "customer_name": name,
            "step": "get_city"
        }

    # 4️⃣ Now we have phone, name, city, salary → register customer
    res = register_agent(phone, name, city, salary)

    msg = (
        f"🎉 **Registration Successful!**\n"
        f"Welcome **{res['name']}** from **{res['city']}**.\n\n"
        f"📄 Your Details:\n"
        f"• 💰 Monthly Salary: **₹{res['salary']:,}**\n"
        f"• 📊 Assigned Credit Score: **{res['credit_score']} / 900**\n"
        f"• 🏦 Pre-Approved Personal Loan Limit: **₹{res['limit']:,}**\n"
        f"• 📉 Existing Monthly EMIs: **₹{res['existing_emi']:,}**\n\n"
        f"🔎 You can now apply for a loan. Tell me the amount you need."
    )

    return {
        "messages": [AIMessage(content=msg)],
        "customer_phone": phone,
        "customer_name": res["name"],
        "customer_city": res["city"],
        "step": "sales"
    }

def sales_node(state: AgentState):
    print("--- AGENT: Sales ---")
    msg_raw = state['messages'][-1].content
    msg = msg_raw.lower()
    current_amt = state.get('loan_amount', 0)

    # Try parsing a new amount
    new_amt = parse_loan_amount(msg_raw)
    if new_amt > 0:
        current_amt = new_amt

    if current_amt == 0:
        return {"messages": [AIMessage(content="Please specify the loan amount (Example: '2 lakh', '50000', '50 thousand').")], "step": "sales"}

    # Persuasion
    if any(w in msg for w in ["high", "expensive", "interest"]) and not state.get("offered_discount"):
        return {
            "messages": [AIMessage(content="I can offer a **0.5% interest discount** if you enable Auto-Pay. Shall we continue?")],
            "offered_discount": True,
            "step": "sales"
        }

    est_emi = calculate_emi(current_amt, 14, 12)
    response_msg = f"""**Loan Summary:**
\n💰 **Amount:** ₹{current_amt}
\n📉 **Interest Rate:** 14% p.a.
\n💵 **Est. EMI:** ₹{est_emi}
\n\n**Shall I generate the Final Sanction Slip?** (Yes/No)"""
    return {
        "messages": [AIMessage(content=response_msg)],
        "loan_amount": current_amt,
        "step": "confirm_deal"
    }

def confirmation_node(state: AgentState):
    msg = state['messages'][-1].content.lower()
    # Negotiation Handling at confirmation stage
    if any(w in msg for w in ["interest", "rate", "too high", "expensive", "less", "reduce"]) and not state.get("offered_discount"):
        new_emi = calculate_emi(state['loan_amount'], 13.5, 12)
        return {
            "messages": [AIMessage(content=f"I can offer **13.5%** with Auto-Pay. New EMI = ₹{new_emi}. Proceed? (Yes/No)")],
            "offered_discount": True,
            "step": "confirm_deal"
        }
    if any(w in msg for w in ["yes", "ok", "confirm", "proceed", "generate"]):
        return {"step": "underwriting"}
    if any(w in msg for w in ["no", "change", "modify", "different amount"]):
        return {"messages": [AIMessage(content="Sure, please enter your new desired loan amount.")], "step": "sales"}
    return {"messages": [AIMessage(content="Please respond with **Yes** to continue or **No** to modify the loan.")], "step": "confirm_deal"}

def underwriting_node(state: AgentState):
    print("--- AGENT: Underwriter ---")
    msg = state['messages'][-1].content.lower()
    phone = state.get('customer_phone')
    amount = state.get('loan_amount', 0)
    has_uploaded = ("upload" in msg or "uploaded" in msg) or check_salary_slip_exists(phone)
    decision = underwriting_agent(phone, amount, salary_slip_uploaded=has_uploaded)
    return {"final_decision": decision, "step": "final_outcome"}

# --- 3. GRAPH CONSTRUCTION ---
workflow = StateGraph(AgentState)
workflow.add_node("router", master_node)
workflow.add_node("verifier", verification_node)
workflow.add_node("register_name", registration_name_node)
workflow.add_node("register_city", registration_city_node)
workflow.add_node("register_salary", registration_salary_node)
workflow.add_node("sales", sales_node)
workflow.add_node("confirmer", confirmation_node)
workflow.add_node("underwriter", underwriting_node)

workflow.set_entry_point("router")

def route_logic(state):
    step = state['step']
    if step == "done": return "stop"
    if step == "waiting_for_phone": return "stop"
    if step == "greet": return "stop"
    return step 

workflow.add_conditional_edges(
    "router",
    route_logic,
    {
        "greet": "router", 
        "verifying": "verifier",
        "get_name": "register_name",
        "get_city": "register_city",
        "get_salary": "register_salary",
        "sales": "sales",
        "confirm_deal": "confirmer",
        "underwriting": "underwriter",
        "final_outcome": "router",
        "stop": END
    }
)

# Interaction nodes wait for user input
workflow.add_edge("verifier", END)
workflow.add_edge("register_name", END)
workflow.add_edge("register_city", END)
workflow.add_edge("register_salary", END)
workflow.add_edge("sales", END)
workflow.add_edge("confirmer", "router")
workflow.add_edge("underwriter", "router")

app_graph = workflow.compile()

# --- 4. EXECUTOR & STATE RECOVERY ---
class GraphExecutor:
    def invoke(self, input_dict):
        """
        input_dict keys:
          - input: str (user message)
          - chat_history: list[BaseMessage] (previous chat messages)
          - session_id: str  (session identifier)
        """
        user_input = (input_dict.get('input') or "").strip()
        hist = input_dict.get('chat_history') or []
        session_id = input_dict.get('session_id')

        # Keep last 50 messages for memory
        recent_hist = hist[-50:] if len(hist) > 50 else hist

        # Quick helper: get concatenated text from recent history
        def full_text(messages):
            try:
                return " ".join([m.content for m in messages])
            except Exception:
                # If DB returns dicts instead of message objects
                return " ".join([m.get("content") if isinstance(m, dict) else str(m) for m in messages])

        full = full_text(recent_hist)
        full_lower = full.lower()

        # ---------------- RECONSTRUCT STATE ----------------
        step = "greet"
        phone = None
        name = None
        amt = 0

        from langchain_core.messages import AIMessage, HumanMessage

        # --- SCAN RECENT AI MESSAGES (most recent first) ---
        # Pick the first relevant AI message we find and set step accordingly.
        found_marker = False
        for m in reversed(recent_hist):
            if not isinstance(m, AIMessage):
                continue
            text = getattr(m, "content", "")
            text_l = text.lower()

            # Priority order: Loan-confirmation, Registration/Verification success,
            # Salary question, City question, Name question
            if "loan summary" in text_l or "est. emi" in text_l or "est. emi:" in text_l:
                step = "confirm_deal"
                # Extract amount only from this AI message (avoid picking digits from EMI)
                m_amount = re.search(r"Amount[:\*\s]*₹\s*([0-9,]+)", text)
                if m_amount:
                    try:
                        amt = int(m_amount.group(1).replace(",", ""))
                    except Exception:
                        amt = 0
                found_marker = True
                break

            if "registration successful" in text_l or "registration complete" in text_l or "verification successful" in text_l:
                step = "sales"
                found_marker = True
                break

            if "monthly salary" in text_l or "what is your monthly salary" in text_l:
                step = "get_salary"
                found_marker = True
                break

            if "which city" in text_l or "which city do you live in" in text_l:
                step = "get_city"
                found_marker = True
                break

            if "what is your full name" in text_l:
                step = "get_name"
                found_marker = True
                break

        # If we didn't find any clear AI marker, fall back to a few heuristics on whole history:
        if not found_marker:
            # if verification/registration words anywhere in history, assume sales
            if "verification successful" in full_lower or "registration complete" in full_lower or "registration successful" in full_lower:
                step = "sales"
            # If the history shows a loan summary somewhere, go confirm_deal
            elif "loan summary" in full_lower or "est. emi" in full_lower:
                step = "confirm_deal"
                # best-effort extraction of amount from history (less ideal but fallback)
                nums = re.findall(r"Amount[:\*\s]*₹\s*([0-9,]+)", full)
                if nums:
                    try:
                        amt = int(nums[-1].replace(",", ""))
                    except:
                        amt = 0
            # If the conversation includes "which city" prompt anywhere and we haven't seen better marker
            elif "which city" in full_lower:
                step = "get_city"
            elif "what is your full name" in full_lower:
                step = "get_name"
            # keep default 'greet' otherwise

        # Underwriting (if salary slip / upload mentioned anywhere in conversation)
        if "upload" in full_lower or "salary slip" in full_lower:
            if step not in ("confirm_deal",):
                step = "underwriting"

        if phone is None:
            digits = re.findall(r"\d{10,}", full)
            if digits:
                phone = digits[-1][-10:]  # last 10 digits of last big number
                
        # (Optional) keep your phone/name shortcuts; they look into history as a fallback
        if "verification successful" in full or "registration complete" in full or "registration successful" in full:
            if "sunny" in full_lower:
                phone, name = "9999999993", "Sunny"
            if "amit" in full_lower:
                phone, name = "9999999991", "Amit"

        # DEBUG print so you can watch what's inferred
        print(f"--- EXECUTOR: inferred step='{step}' | amt={amt} | last_ai_sample='{(recent_hist[-1].content[:80] if recent_hist else '')}'")

        # ---------------- RESUME / START-NEW LOGIC ----------------
        ui_lc = user_input.lower()

        unfinished_steps = {
            "confirm_deal",
            "underwriting",
            "sales",
            "waiting_for_phone",
            "get_name",
            "get_city",
            "get_salary",
        }
        is_unfinished = step in unfinished_steps

        simple_greetings = {"hi", "hey", "hello", "hey there"}
        if ui_lc in simple_greetings and is_unfinished:
            prompt = ("It looks like you were in the middle of a loan application earlier. "
                      "Would you like to *resume* where you left off or *start new*? "
                      "Reply with 'resume' or 'start new'.")
            return {"output": prompt}

        if ui_lc in {"resume", "continue", "yes resume", "resume please", "continue please"} and is_unfinished:
            initial_state = {
                "messages": recent_hist + [HumanMessage(content=user_input)],
                "step": step,
                "customer_phone": phone,
                "customer_name": name,
                "loan_amount": amt,
                "offered_discount": False,
                "final_decision": {}
            }
            result = app_graph.invoke(initial_state)
            if not result.get('messages'):
                return {"output": "System Error: No response generated."}
            return {"output": result['messages'][-1].content}

        if ui_lc in {"start new", "new", "start over", "reset session"}:
            registered = (
                "Registration Complete" in full
                or "Verification Successful" in full
                or "Registration Successful" in full
            )
            if registered:
                initial_state = {
                    "messages": recent_hist + [HumanMessage(content=user_input)],
                    "step": "sales",
                    "customer_phone": phone,
                    "customer_name": name,
                    "loan_amount": 0,
                    "offered_discount": False,
                    "final_decision": {}
                }
                result = app_graph.invoke(initial_state)
                if not result.get('messages'):
                    return {"output": "System Error: No response generated."}
                return {"output": result['messages'][-1].content}
            else:
                initial_state = {
                    "messages": recent_hist + [HumanMessage(content=user_input)],
                    "step": "greet",
                    "customer_phone": None,
                    "customer_name": None,
                    "loan_amount": 0,
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
            "offered_discount": False,
            "final_decision": {}
        }

        result = app_graph.invoke(initial_state)
        if not result.get('messages'):
            return {"output": "System Error: No response generated."}
        return {"output": result['messages'][-1].content}

agent_executor = GraphExecutor()
