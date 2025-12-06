from fpdf import FPDF
import os

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'TATA CAPITAL - SANCTION LETTER', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_sanction_letter(customer_name, phone, amount, emi, tenure):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Content
    content = [
        f"Date: 2024-10-25",
        f"To: {customer_name}",
        f"Phone: {phone}",
        "",
        "Subject: In-Principle Sanction of Personal Loan",
        "",
        f"Dear {customer_name},",
        "",
        "We are pleased to inform you that your personal loan application has been approved based on the details provided.",
        "",
        "--- LOAN DETAILS ---",
        f"Approved Amount: INR {amount}",
        f"Interest Rate: 14% p.a.",
        f"Tenure: {tenure} Months",
        f"Monthly EMI: INR {emi}",
        "",
        "This is a system-generated letter and does not require a physical signature.",
        "",
        "Best Regards,",
        "Tata Capital AI Team"
    ]
    
    for line in content:
        pdf.cell(0, 10, txt=line, ln=1)
        
    # Ensure directory exists
    if not os.path.exists("static_pdfs"):
        os.makedirs("static_pdfs")
        
    filename = f"static_pdfs/{phone}_sanction.pdf"
    pdf.output(filename)
    return filename