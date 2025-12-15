# main.py
import os
import shutil
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from help import router as help_router

# Import Agent & DB
from master_agent import agent_executor
import database

app = FastAPI(title="Tata Capital Agent API")

# -------------------- CORS CONFIGURATION --------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:3000",  # Common React dev port
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    user_input = (request.message or "").strip()

    try:
        # Fetch past messages for that user-session
        history = database.get_chat_history(session_id)

        # --- DEDUP CHECK: if identical to last human message, return last AI reply ---
        last_human = None
        last_ai = None
        # history assumed to be list of dicts like {"role": "human"/"ai", "content": "..."}
        for m in reversed(history):
            role = m.get("role") if isinstance(m, dict) else None
            content = m.get("content") if isinstance(m, dict) else getattr(m, "content", None)
            if not last_human and role == "human" and content is not None:
                last_human = content.strip()
            if not last_ai and role == "ai" and content is not None:
                last_ai = content
            if last_human and last_ai:
                break

        if last_human and user_input and last_human.lower() == user_input.lower():
            # Duplicate user message — avoid re-processing.
            # Return the last AI response (if any). Do NOT save duplicate human message.
            if last_ai:
                return {"response": last_ai}
            else:
                # No previous AI reply found — fall back to processing
                pass

        # Run Agent
        response = agent_executor.invoke({
            "input": user_input,
            "chat_history": history,
            "session_id": session_id,
            "tenure": request.tenure or 12
        })

        bot_response = response['output']

        # Save to DB (only AFTER agent produced a response)
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
    
app.include_router(help_router)

