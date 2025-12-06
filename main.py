from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage

# Import the agent executor we built in Phase 3
# Ensure your master_agent.py file is in the same folder
from master_agent import agent_executor

app = FastAPI(title="Tata Capital Agent API")

# --- IN-MEMORY SESSION STORAGE ---
# In a real production app, use Redis or a Database.
# For this hackathon, a dictionary is fine.
# Format: { "session_id": [ message_history ] }
chat_sessions = {}

# --- REQUEST MODEL ---
class ChatRequest(BaseModel):
    session_id: str  # A unique ID for the user (e.g., "user1")
    message: str     # The text they typed

@app.get("/")
def home():
    return {"status": "Active", "message": "Tata Capital Agent Backend is running."}

@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    session_id = request.session_id
    user_input = request.message
    
    # 1. Retrieve or Initialize Chat History
    if session_id not in chat_sessions:
        chat_sessions[session_id] = []
    
    history = chat_sessions[session_id]
    
    # 2. Run the Agent Logic
    try:
        print(f"Processing message for {session_id}: {user_input}")
        
        # We pass the existing history to the agent
        response = agent_executor.invoke({
            "input": user_input,
            "chat_history": history
        })
        
        bot_response = response['output']
        
        # 3. Update History
        history.append(HumanMessage(content=user_input))
        history.append(AIMessage(content=bot_response))
        
        return {
            "response": bot_response,
            "session_id": session_id
        }
        
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Run this using: uvicorn api:app --reload