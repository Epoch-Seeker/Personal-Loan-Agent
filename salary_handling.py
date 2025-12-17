import os
from langchain_google_genai import ChatGoogleGenerativeAI
from pypdf import PdfReader  # pip install pypdf
from typing import BinaryIO
from dotenv import load_dotenv

load_dotenv()

# 1. Configure Gemini
# Make sure GEMINI_API_KEY is set in your environment.
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

def extract_text_from_payslip(file_obj: BinaryIO) -> str:
    """
    Extract all text from a PDF salary slip uploaded as a file-like object.
    Example usage with FastAPI:
        text = extract_text_from_payslip(uploaded_file.file)
    """
    reader = PdfReader(file_obj)
    text_chunks = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        text_chunks.append(page_text)
    return "\n".join(text_chunks)


def get_monthly_salary_from_payslip(file_obj: BinaryIO) -> float:
    """
    End-point style function:
    - takes uploaded salary slip (file-like object, e.g. from FastAPI UploadFile.file)
    - extracts text
    - sends text to Gemini 2.5 Flash
    - returns numeric monthly salary (float)
    """
    # Step 1: Extract text
    payslip_text = extract_text_from_payslip(file_obj)

    # Step 2: Ask Gemini to return ONLY the numeric salary
    prompt = f"""
You are given the full text of an employee salary slip.
From this text, identify the employee's monthly take-home salary (net pay).
Return ONLY the number, without any currency symbol or extra text.
If there are multiple months or values, choose the main monthly net salary.

Payslip text:
\"\"\"{payslip_text}\"\"\"
"""

    # model = genai.GenerativeModel("gemini-2.5-flash")
    response = llm.invoke(prompt)

    # Response text should be something like "53421.50" or "45000"
    raw = (response.text or "").strip()

    # Optional: clean commas etc.
    raw = raw.replace(",", "")
    try:
        salary = float(raw)
    except ValueError:
        # If parsing fails, you can handle/log it as you like.
        raise ValueError(f"Model did not return a pure number: {raw!r}")

    return salary
