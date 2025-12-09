# main.py
import os
import shutil
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Import Agent & DB
from master_agent import agent_executor
import database

app = FastAPI(title="Tata Capital Agent API")

# -------------------- Required Folders --------------------
os.makedirs("uploads", exist_ok=True)       # For salary slips
os.makedirs("static_pdfs", exist_ok=True)   # For sanction letter PDFs

# Serve PDFs publicly
app.mount("/pdfs", StaticFiles(directory="static_pdfs"), name="pdfs")


# -------------------- RUN DB ON STARTUP --------------------
@app.on_event("startup")
def startup_event():
    database.init_db()


# -------------------- REQUEST MODELS --------------------
class ChatRequest(BaseModel):
    session_id: str
    message: str
    tenure: int | None = None


@app.get("/")
def home():
    return {"status": "OK", "agent": "Loan Bot Ready 🚀"}


# ==========================================================
#                       CHAT API
# ==========================================================
@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    session_id = request.session_id
    user_input = request.message

    try:
        # Fetch past messages for that user-session
        history = database.get_chat_history(session_id)

        # Run Agent (NO salary logic needed now)
        response = agent_executor.invoke({
            "input": user_input,
            "chat_history": history,
            "session_id": session_id,
            "tenure": request.tenure or 12
        })
        
        bot_response = response['output']

        # Save to DB
        database.save_message(session_id, "human", user_input)
        database.save_message(session_id, "ai", bot_response)

        return {"response": bot_response}

    except Exception as e:
        print(f"[CHAT ERROR] {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================================
#                    SALARY SLIP UPLOAD API
# ==========================================================
# User uploads PDF BEFORE confirmation or when bot requests salary slip.
# filename saved as "<phone>_salary_slip.pdf"
@app.post("/upload")
async def upload_file(phone: str, file: UploadFile = File(...)):
    try:
        filepath = f"uploads/{phone}_salary_slip.pdf"
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        print(f"📄 [UPLOAD SUCCESS] -> {filepath}")
        return {"status": True, "msg": "Salary Slip uploaded successfully"}

    except Exception as e:
        print(f"[UPLOAD ERROR] {e}")
        raise HTTPException(status_code=500, detail=str(e))

