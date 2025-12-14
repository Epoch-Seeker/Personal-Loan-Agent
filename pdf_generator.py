from fpdf import FPDF
import os
from datetime import datetime
from mock_data import INTEREST_RATE

class PDF(FPDF):
    def header(self):
        # Add Tata Capital logo at the top
        logo_path = "assets/tc_logo.png"
        if os.path.exists(logo_path):
            # Logo dimensions: 1011x205 pixels
            # Scale to fit width of 60mm while maintaining aspect ratio
            logo_width = 60
            logo_height = logo_width * (205 / 1011)  # Maintain aspect ratio
            
            # Center the logo
            x_position = (210 - logo_width) / 2  # A4 width is 210mm
            self.image(logo_path, x=x_position, y=10, w=logo_width, h=logo_height)
            self.ln(logo_height + 5)  # Space after logo
        
        # Title
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'LOAN SANCTION LETTER', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()} | Tata Capital Limited | www.tatacapital.com', 0, 0, 'C')

def create_sanction_letter(customer_name, phone, amount, emi, tenure):
    pdf = PDF()
    pdf.add_page()
    pdf.set_left_margin(15)  # Set left margin to prevent overflow
    pdf.set_right_margin(15)  # Set right margin for better layout
    
    # Use current date
    current_date = datetime.now().strftime("%B %d, %Y")
    
    # Date and Reference
    pdf.set_font("Arial", size=10)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 6, f"Date: {current_date}", 0, 1)
    pdf.cell(0, 6, f"Reference No: TC/{phone}/{datetime.now().strftime('%Y%m%d')}", 0, 1)
    pdf.ln(5)
    
    # Recipient details
    pdf.set_font("Arial", 'B', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, "To:", 0, 1)
    pdf.set_font("Arial", size=11)
    pdf.cell(0, 6, customer_name, 0, 1)
    pdf.cell(0, 6, f"Mobile: {phone}", 0, 1)
    pdf.ln(5)
    
    # Subject
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 6, "Subject: In-Principle Sanction of Personal Loan", 0, 1)
    pdf.ln(3)
    
    # Greeting
    pdf.set_font("Arial", size=11)
    pdf.cell(0, 6, f"Dear {customer_name},", 0, 1)
    pdf.ln(3)
    
    # Body text with proper wrapping
    pdf.multi_cell(0, 6, "We are pleased to inform you that your personal loan application has been approved in principle, subject to final documentation and verification. Below are the details of your sanctioned loan:")
    pdf.ln(5)
    
    # Loan Details Box
    pdf.set_fill_color(240, 248, 255)  # Light blue background
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(0, 51, 102)  # Dark blue
    pdf.cell(0, 8, "LOAN DETAILS", 0, 1, 'C', True)
    pdf.ln(2)
    
    # Loan details table
    pdf.set_font("Arial", 'B', 10)
    pdf.set_text_color(0, 0, 0)
    
    details = [
        ("Approved Amount:", f"INR {amount:,}"),
        ("Interest Rate:", f"{INTEREST_RATE}% per annum"),
        ("Loan Tenure:", f"{tenure} Months"),
        ("Monthly EMI:", f"INR {emi:,.2f}"),
        ("Processing Fee:", "As per terms"),
        ("Disbursement:", "Within 24-48 hours")
    ]
    
    for label, value in details:
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(70, 6, label, 0, 0)
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 6, value, 0, 1)
    
    pdf.ln(5)
    
    # Terms and Conditions
    pdf.set_font("Arial", 'B', 11)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 6, "Terms and Conditions:", 0, 1)
    pdf.set_font("Arial", size=9)
    pdf.set_text_color(0, 0, 0)
    
    terms = [
        "EMI payment is due on the 5th of every month",
        "Late payment fee of 2% of EMI amount will be charged for delays",
        "Prepayment is allowed after 6 months from disbursement date",
        "This sanction is valid for 30 days from the date of issuance",
        "Final disbursement is subject to verification of documents",
        "Please refer to the loan agreement for complete terms"
    ]
    
    for i, term in enumerate(terms, 1):
        pdf.multi_cell(0, 5, f"{i}. {term}")
    
    pdf.ln(5)
    
    # Closing
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 6, "We look forward to serving you and helping you achieve your financial goals. For any queries, please contact our customer service.")
    pdf.ln(5)
    
    # Signature section
    pdf.set_font("Arial", 'I', 9)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(0, 6, "This is a system-generated document and does not require a physical signature.", 0, 1)
    pdf.ln(3)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, "Best Regards,", 0, 1)
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 6, "Tata Capital Limited", 0, 1)
    pdf.set_font("Arial", 'I', 9)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 6, "Digital Lending Platform", 0, 1)
    
    # Ensure directory exists
    if not os.path.exists("static_pdfs"):
        os.makedirs("static_pdfs")
        
    filename = f"static_pdfs/{phone}_sanction.pdf"
    pdf.output(filename)
    return filename