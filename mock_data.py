# mock_data.py
import json
import os
import random
import pytesseract
import pdfplumber 
import cv2
import os
import re

DATA_FILE = "customers.json"

# ----------------------- CONSTANTS -----------------------
INTEREST_RATE = 12  # Standardized interest rate (12% p.a.)


# --- LOAD / SAVE -------------------------------------------------------------

def _load_customers_from_file():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    # Seed customers with address for KYC verification
    return [
        {
            "phone": "9999999991",
            "name": "Amit Sharma",
            "city": "Mumbai",
            "address": "Flat 12B, Sea View Apartments, Andheri West, Mumbai 400053",
            "existing_emi": 10000,
            "credit_score": 780,
            "pre_approved_limit": 500000,
        },
        {
            "phone": "9999999992",
            "name": "Priya Patel",
            "city": "Delhi",
            "address": "House No. 45, Sector 22, Dwarka, New Delhi 110077",
            "existing_emi": 5000,
            "credit_score": 820,
            "pre_approved_limit": 800000,
        },
        {
            "phone": "9999999993",
            "name": "Sunny Kumar",
            "city": "Pune",
            "address": "201 Harmony Heights, Baner Road, Pune 411045",
            "existing_emi": 12000,
            "credit_score": 750,
            "pre_approved_limit": 500000,
        },
        {
            "phone": "9999999994",
            "name": "Rajesh Verma",
            "city": "Bangalore",
            "address": "42, 3rd Cross, Indiranagar, Bangalore 560038",
            "existing_emi": 0,
            "credit_score": 650,
            "pre_approved_limit": 300000,
        },
        {
            "phone": "9999999995",
            "name": "Sneha Reddy",
            "city": "Hyderabad",
            "address": "Plot 78, Jubilee Hills Road No. 10, Hyderabad 500033",
            "existing_emi": 8000,
            "credit_score": 800,
            "pre_approved_limit": 700000,
        },
        {
            "phone": "9999999996",
            "name": "Vikram Singh",
            "city": "Chennai",
            "address": "15A, Anna Nagar East, Chennai 600102",
            "existing_emi": 15000,
            "credit_score": 720,
            "pre_approved_limit": 450000,
        },
        {
            "phone": "9999999997",
            "name": "Anita Desai",
            "city": "Kolkata",
            "address": "Flat 5C, Park Street Residency, Kolkata 700016",
            "existing_emi": 3000,
            "credit_score": 850,
            "pre_approved_limit": 1000000,
        },
        {
            "phone": "9999999998",
            "name": "Rahul Mehta",
            "city": "Ahmedabad",
            "address": "B-102, Swastik Heights, Navrangpura, Ahmedabad 380009",
            "existing_emi": 20000,
            "credit_score": 680,
            "pre_approved_limit": 350000,
        },
        {
            "phone": "9999999999",
            "name": "Kavita Joshi",
            "city": "Jaipur",
            "address": "56, Malviya Nagar, Jaipur 302017",
            "existing_emi": 6000,
            "credit_score": 760,
            "pre_approved_limit": 550000,
        },
        {
            "phone": "9999999900",
            "name": "Arjun Nair",
            "city": "Kochi",
            "address": "TC 12/456, Marine Drive, Ernakulam, Kochi 682031",
            "existing_emi": 0,
            "credit_score": 790,
            "pre_approved_limit": 600000,
        },
    ]


def _save_customers_to_file(customers):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(customers, f, indent=2)


CUSTOMERS = _load_customers_from_file()


# --- SALARY SLIP SIMULATION --------------------------------------------------
# dependencies: pip install pymupdf pillow pytesseract opencv-python
# On Windows: install Tesseract-OCR and set pytesseract.pytesseract.tesseract_cmd accordingly

import os
import re
import fitz  # pymupdf
import pytesseract
from PIL import Image
import io
import numpy as np
import cv2

# If you installed Tesseract on Windows, set the path, e.g.
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def _pdf_first_page_to_pil(pdf_path, zoom=2):
    """Render first page of PDF to a PIL.Image (RGB)."""
    doc = fitz.open(pdf_path)
    if doc.page_count < 1:
        doc.close()
        raise RuntimeError("PDF has no pages")
    page = doc.load_page(0)
    mat = fitz.Matrix(zoom, zoom)  # zoom to increase resolution for OCR
    pix = page.get_pixmap(matrix=mat, alpha=False)  # RGB
    img_bytes = pix.tobytes("png")
    doc.close()
    return Image.open(io.BytesIO(img_bytes))

def _pil_to_cv2(pil_img):
    """Convert PIL.Image (RGB) to OpenCV BGR ndarray safely."""
    if pil_img.mode != "RGB":
        pil_img = pil_img.convert("RGB")
    arr = np.array(pil_img)            # RGB
    bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
    return bgr

def extract_salary_from_slip(phone: str) -> int:
    """
    Extract monthly salary (int) from uploaded salary slip PDF or image.
    Returns integer monthly salary if found, else 0.
    """
    if not phone:
        print("[ERROR] extract_salary_from_slip called without phone")
        return 0

    uploads_dir = os.path.join("uploads")
    pdf_path = os.path.abspath(os.path.join(uploads_dir, f"{phone}_salary_slip.pdf"))
    img_path_jpg = os.path.abspath(os.path.join(uploads_dir, f"{phone}_salary_slip.jpg"))
    img_path_png = os.path.abspath(os.path.join(uploads_dir, f"{phone}_salary_slip.png"))

    # choose path: prefer pdf then jpg/png
    if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
        source_type = "pdf"
        source_path = pdf_path
    elif os.path.exists(img_path_jpg) and os.path.getsize(img_path_jpg) > 0:
        source_type = "image"
        source_path = img_path_jpg
    elif os.path.exists(img_path_png) and os.path.getsize(img_path_png) > 0:
        source_type = "image"
        source_path = img_path_png
    else:
        print(f"[ERROR] extract_salary_from_slip: no file found for phone={phone}. "
              f"Checked: {pdf_path}, {img_path_jpg}, {img_path_png}")
        return 0

    print(f"[DEBUG] extract_salary_from_slip: using {source_type} at {source_path}")

    try:
        if source_type == "pdf":
            pil_img = _pdf_first_page_to_pil(source_path, zoom=2)
            cv_img = _pil_to_cv2(pil_img)
        else:
            # image file: load with OpenCV (safer than imread direct on weird encodings)
            # but check file size first
            size = os.path.getsize(source_path)
            if size == 0:
                print(f"[ERROR] file {source_path} has zero size.")
                return 0
            # use pillow to ensure format support, then convert
            pil_img = Image.open(source_path)
            cv_img = _pil_to_cv2(pil_img)

        if cv_img is None or cv_img.size == 0:
            print("[ERROR] image conversion failed; image empty")
            return 0

        # optional: preprocess for better OCR
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        # threshold to clean the background - tweak if needed
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # OCR: use PIL image for pytesseract (convert back)
        ocr_pil = Image.fromarray(cv2.cvtColor(thresh, cv2.COLOR_GRAY2RGB))
        text = pytesseract.image_to_string(ocr_pil, lang="eng")
        text_lower = text.lower()
        print(f"[DEBUG] OCR text snippet: {text_lower[:200]}")

        # regex: look for monthly salary / numbers labelled monthly/per month
        # Common patterns: "₹ 50,000", "50000 per month", "monthly salary 50,000"
        patterns = [
            r"(?:monthly salary|salary per month|salary|net in hand|in-hand)[^\d\n\r]{0,30}([\d,]{3,})",
            r"([\d,]{3,})\s*(?:/month|per month|pm|monthly)",
            r"₹\s*([\d,]+)"
        ]
        for p in patterns:
            m = re.search(p, text_lower, flags=re.IGNORECASE)
            if m:
                num_s = m.group(1).replace(",", "")
                try:
                    val = int(re.sub(r"\D", "", num_s))
                    print(f"[INFO] Extracted salary: {val}")
                    return val
                except:
                    continue

        # fallback: find largest 5+ digit number in the text (heuristic)
        nums = re.findall(r"[\d,]{5,}", text_lower)
        if nums:
            nums_clean = [int(n.replace(",", "")) for n in nums]
            val = max(nums_clean)
            print(f"[INFO] Heuristic salary guess: {val}")
            return val

        print("[WARN] No salary number found in OCR output.")
        return 0

    except Exception as e:
        print(f"[ERROR] extract_salary_from_slip exception: {e}")
        return 0

# --- ADDRESS GENERATION FOR NEW CUSTOMERS ------------------------------------

def _generate_random_address(city: str) -> str:
    """Generate a realistic-looking address for new customers."""
    street_types = ["Street", "Road", "Lane", "Avenue", "Marg", "Nagar"]
    building_types = ["Flat", "House No.", "Plot", "Unit"]
    areas = ["Sector 15", "Block A", "Phase 2", "West Wing", "East Block", "Central"]
    
    building = f"{random.choice(building_types)} {random.randint(1, 500)}"
    area = random.choice(areas)
    street = f"{random.choice(['Main', 'Park', 'Lake', 'Hill', 'Green'])} {random.choice(street_types)}"
    pincode = random.randint(100001, 999999)
    
    return f"{building}, {area}, {street}, {city} {pincode}"


# --- API ---------------------------------------------------------------------

def get_customer_by_phone(phone: str):
    for cust in CUSTOMERS:
        if cust["phone"] == phone:
            return cust
    return None


def create_new_customer(phone: str, name: str, city: str, address: str = None):
    """
    Create customer with address for KYC.
    Salary slip will be required during underwriting.
    """

    credit_score = random.randint(700, 850)            # Random fair-good score
    pre_limit = random.choice([300000, 400000, 500000]) # Give a base limit
    existing_emi = random.randint(0, 15000)             # Random EMI
    
    # Generate address if not provided
    if not address:
        address = _generate_random_address(city)

    new_customer = {
        "phone": phone,
        "name": name,
        "city": city,
        "address": address,
        "credit_score": credit_score,
        "pre_approved_limit": pre_limit,
        "existing_emi": existing_emi
    }

    CUSTOMERS.append(new_customer)
    _save_customers_to_file(CUSTOMERS)

    return new_customer
