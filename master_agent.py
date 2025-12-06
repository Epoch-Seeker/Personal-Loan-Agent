import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import tool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage # <--- Added for Memory
from dotenv import load_dotenv

load_dotenv()

# Import your worker logic
from agents import verification_agent, underwriting_agent, check_salary_slip_exists
from pdf_generator import create_sanction_letter


@tool
def verify_customer_tool(phone_number: str):
    """
    Call this tool FIRST to verify the customer exists in the database.
    Input: The customer's 10-digit phone number.
    """
    return verification_agent(phone_number)

@tool
def underwriting_tool(phone_number: str, loan_amount: int):
    """
    Call this to check loan eligibility.
    If the amount is high, it AUTOMATICALLY checks if the salary slip 
    has been uploaded to the server.
    """
    # 1. Check if slip exists on disk
    is_slip_uploaded = check_salary_slip_exists(phone_number)
    
    # 2. Call the logic
    return underwriting_agent(phone_number, loan_amount, salary_slip_uploaded=is_slip_uploaded)

@tool
def generate_sanction_letter_tool(phone: str, amount: int):
    """
    Generates a REAL PDF sanction letter.
    Call this ONLY if the loan status is APPROVED.
    Input: Phone number and Amount.
    """
    # We need to fetch the name and EMI again or pass it. 
    # For simplicity, let's fetch basic details
    from mock_data import get_customer_by_phone
    from agents import calculate_emi
    
    user = get_customer_by_phone(phone)
    if not user: return "Error: User not found"
    
    emi = calculate_emi(amount, 14, 12) # Assuming 12 months default
    
    # Generate the actual PDF file
    pdf_path = create_sanction_letter(user['name'], phone, amount, emi, 12)
    
    # Return the clickable URL (Assuming local server)
    filename = os.path.basename(pdf_path)
    return f"SUCCESS: Loan Sanctioned! Download Letter here: http://127.0.0.1:8000/pdfs/{filename}"

tools = [verify_customer_tool, underwriting_tool, generate_sanction_letter_tool]

# --- INITIALIZE GEMINI ---
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0
)

# --- CREATE THE PROMPT WITH MEMORY ---
# We added 'chat_history' so the agent remembers previous messages
prompt = ChatPromptTemplate.from_messages([
    ("system", 
     """You are a helpful and persuasive Sales Assistant for Tata Capital. 
     Your goal is to help customers get a personal loan.
     
     FOLLOW THIS PROCESS STRICTLY:
     1. Greet the user and ask for their Phone Number to verify their identity.
     2. Use the 'verify_customer_tool'.
     3. If verified, ask them how much loan amount they need.
     4. Use the 'underwriting_tool' to check eligibility.
     5. If the result says "NEEDS_DOCS", ask the user to upload their Salary Slip (simulate this by asking them to type 'I have uploaded the slip').
     6. If APPROVED, use the 'generate_sanction_letter_tool' and close the sale.
     7. If REJECTED, be polite and explain the reason (e.g. Low Credit Score).
     
     Do not make up information. Always use the tools to get data.
     """),
    MessagesPlaceholder(variable_name="chat_history"), # <--- MEMORY SLOT
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# --- MAIN LOOP (Chat Interface) ---
def start_chat():
    print("--- TATA CAPITAL AI AGENT STARTED (With Memory) ---")
    print("(Type 'quit' to exit)")
    
    chat_history = [] # Initialize empty memory
    
    while True:
        user_input = input("\nUser: ")
        if user_input.lower() in ["quit", "exit"]:
            break
            
        # Pass the history AND the new input
        response = agent_executor.invoke({
            "input": user_input,
            "chat_history": chat_history
        })
        
        output_text = response['output']
        print(f"Agent: {output_text}")
        
        # Update Memory
        chat_history.append(HumanMessage(content=user_input))
        chat_history.append(AIMessage(content=output_text))

if __name__ == "__main__":
    start_chat()