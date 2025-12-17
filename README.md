# 🏦 AI-Powered Loan Assistant

> **Built for EY Techathon**
> *Revolutionizing the digital lending experience with GenAI.*

## 1. Project Title
**Loan Bot - Intelligent Digital Lending Assistant**

## 2. Project Overview
This project is an AI-driven conversational agent designed to streamline the loan application process for banks and financial institutions. It replaces static forms with an interactive, natural language interface that guides users from eligibility checks to final sanction letter generation.

### 🚀 What problem this project solves
- **Eliminates complex paperwork:** Users can apply for loans through a simple chat.
- **Instant Eligibility Checks:** Real-time analysis of credit scores and income.
- **Automated Underwriting:** Intelligent decision-making based on financial data.
- **24/7 Availability:** Always-on assistant for customer queries.

### 👥 Who this project is for
- **Bank Customers:** Seeking quick, hassle-free loans (Personal, Home, etc.).
- **Loan Officers:** To automate initial screening and document verification.
- **FinTech Developers:** As a reference for building GenAI-powered banking apps.

## 3. Features
- **🤖 GenAI Chatbot:** Powered by Google Gemini for human-like conversations.
- **🆔 Automated KYC:** Verifies identity via phone number (simulated).
- **📄 Document Analysis:** Parses uploaded salary slips (PDF) to verify income.
- **💰 Smart Loan Offers:** Generates dynamic offers based on credit score and salary.
- **🖨️ PDF Generation:** Auto-generates official Sanction Letters upon approval.
- **🎙️ Voice Interaction:** Supports voice commands for accessibility.
- **📊 Interactive UI Cards:** Displays loan summaries, approvals, and rejections visually.

## 4. System Architecture
The system follows a modern client-server architecture:

- **Frontend:** A responsive Single Page Application (SPA) that handles user interaction, chat rendering, and file uploads. It parses structured JSON tags from the bot to render rich UI components (cards).
- **Backend:** A robust FastAPI server that manages session state, orchestrates AI agents, processes logic (underwriting), and handles file operations.
- **AI Engine:** Google Gemini Pro acts as the "brain," interpreting user intent and generating natural responses.
- **Storage:** SQLite for chat history and local file system for generated PDFs and uploaded documents.

## 5. Tech Stack

### Frontend
- **Framework:** React 18 + Vite
- **Language:** TypeScript
- **Styling:** Tailwind CSS + Shadcn UI
- **State/Routing:** React Router, Axios, React Query
- **Extras:** React Speech Recognition, React Markdown

### Backend
- **Framework:** FastAPI (Python)
- **Server:** Uvicorn
- **PDF Processing:** ReportLab, PyPDF2
- **AI Integration:** Google Generative AI (Gemini), LangChain

### Database / Storage
- **Database:** SQLite (Chat History)
- **File Storage:** Local filesystem (`/uploads`, `/static_pdfs`)

## 6. Project Flow
1. **User Login:** User enters their phone number to start.
2. **KYC Check:** Bot verifies the user against the database (mock data).
3. **Credit Analysis:** System checks credit score and pre-approved limits.
4. **Needs Assessment:** Bot asks for loan amount and purpose.
5. **Eligibility Calculation:**
   - If amount < Pre-approved Limit → **Instant Offer**.
   - If amount > Limit → **Requests Salary Slip**.
6. **Document Verification:** User uploads PDF → Backend parses income using AI.
7. **Underwriting Decision:**
   - **Approved:** Generates Sanction Letter PDF.
   - **Soft Reject:** Offers lower amount based on EMI capacity.
   - **Hard Reject:** If credit score is too low.
8. **Completion:** User downloads the sanction letter.

## 7. Installation & Setup

### Prerequisites
- Python 3.9+
- Node.js 18+
- Google Gemini API Key

### Backend Setup
1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd <repo-folder>
   ```
2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   # Create a requirements.txt with the following or install directly:
   pip install fastapi uvicorn google-generativeai langchain-google-genai reportlab python-multipart pypdf python-dotenv
   ```
4. Create a `.env` file in the root:
   ```env
   GOOGLE_API_KEY=your_gemini_api_key
   ```
5. Run the server:
   ```bash
   uvicorn main:app --reload
   ```

### Frontend Setup
1. Navigate to the frontend folder:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```

## 8. Environment Variables
Create a `.env` file in the project root with the following keys:

| Variable | Description |
|----------|-------------|
| `GOOGLE_API_KEY` | Required. API key for Google Gemini AI. Get it from Google AI Studio. |

## 9. API Endpoints
| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/` | Health check to verify server status. |
| `POST` | `/chat` | Main conversational endpoint (handles messages & context). |
| `POST` | `/upload` | Uploads salary slip PDF for income verification. |
| `GET` | `/pdfs/{filename}` | Downloads the generated sanction letter. |

## 10. Usage Guide
1. Open the frontend URL (e.g., `http://localhost:8080`).
2. Type **"Hi"** to start the conversation.
3. Enter a registered phone number (e.g., `9999999991` for approval, `9999999994` for rejection).
4. Follow the bot's prompts to select a loan amount and tenure.
5. If prompted, upload a sample PDF salary slip.
6. View the generated **Loan Offer Card** and download the **Sanction Letter**.

## 11. Folder Structure
```
├── frontend/          # React frontend application
├── assets/            # Static assets
├── uploads/           # User uploaded documents
├── static_pdfs/       # Generated sanction letters
├── main.py            # FastAPI entry point
├── agents.py          # AI agent definitions
├── master_agent.py    # Orchestrator for AI agents
├── pdf_generator.py   # PDF creation logic
├── salary_handling.py # Salary parsing logic
├── customers.json     # Mock customer data
├── database.py        # Database operations
└── API_DOCUMENTATION.md # Detailed API docs
```

## 12. Screenshots / Demo
*(Placeholders for screenshots)*

- **Login Interface:** ![Login UI](Screeenshots\login_interface.png)
- **Home Interface:** ![Customer Home UI](Screeenshots\customer_home.png)
- **Chat Interface:** ![Chat UI](Screeenshots\chat.png)
- **Loan Offer Card:** ![Loan Offer](Screeenshots\loan_offer_card.png)
- **Sanction Letter:** ![Sanction Letter](Screeenshots\sanction_letter.png)

## 13. Future Improvements
- **OCR Integration:** Use AWS Textract or Google Vision for real document scanning.
- **Authentication:** Implement JWT-based user login.
- **Bank API Integration:** Connect to real core banking systems.
- **Multi-language Support:** Use Gemini to support regional languages.

## 14. Known Issues / Limitations
- **Mock Data:** Uses `customers.json` instead of a real banking database.
- **Session Persistence:** Chat history is local (SQLite) and not tied to persistent user accounts.
- **PDF Parsing:** Basic implementation; may not work with complex salary slip formats.

## 15. License
This project is licensed under the **MIT License**.
