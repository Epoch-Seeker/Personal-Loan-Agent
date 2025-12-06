# api.py
import os
import shutil
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Import Agent and Database
from master_agent import agent_executor
from pdf_generator import create_sanction_letter
import database

app = FastAPI(title="Tata Capital Agent API")

# --- FIX: CREATE FOLDERS IMMEDIATELY ---
# These must exist BEFORE app.mount is called
os.makedirs("uploads", exist_ok=True)
os.makedirs("static_pdfs", exist_ok=True)

# --- MOUNT FOLDERS ---
app.mount("/pdfs", StaticFiles(directory="static_pdfs"), name="pdfs")

# --- DATABASE SETUP ---
@app.on_event("startup")
def startup_event():
    database.init_db()

# --- MODELS ---
class ChatRequest(BaseModel):
    session_id: str
    message: str

# --- ENDPOINTS ---
@app.get("/")
def home():
    return {"status": "Online", "storage": "SQLite Database"}

@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    session_id = request.session_id
    user_input = request.message
    
    try:
        # Load History
        history = database.get_chat_history(session_id)
        
        # Run Agent
        response = agent_executor.invoke({
            "input": user_input,
            "chat_history": history
        })
        bot_response = response['output']
        
        # Save History
        database.save_message(session_id, "human", user_input)
        database.save_message(session_id, "ai", bot_response)
        
        return {"response": bot_response}
        
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload")
async def upload_file(phone: str, file: UploadFile = File(...)):
    try:
        file_location = f"uploads/{phone}_salary_slip.pdf"
        with open(file_location, "wb+") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return {"status": "success", "message": "File uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))