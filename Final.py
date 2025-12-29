import streamlit as st
from fpdf import FPDF
import pandas as pd
from num2words import num2words
import datetime
import io
from PIL import Image
import os
from fpdf import FPDF, HTMLMixin
import textwrap
import html as _html 
import json
import requests

# GitHub Configuration - EMPTY PLACEHOLDERS
LOGO_URL = ""  # Remove your GitHub URL
STAMP_URL = ""  # Remove your GitHub URL

# --- Global Data and Configuration ---
PRODUCT_CATALOG = {
    "Software Product 1": {"basic": 10000.0, "gst_percent": 18.0},
    "Software Product 2": {"basic": 20000.0, "gst_percent": 18.0},
    "Software Product 3": {"basic": 30000.0, "gst_percent": 18.0},
    "Software Service": {"basic": 5000.0, "gst_percent": 18.0},
}

# Load data from JSON files
def load_json_data(filename, default_data=None):
    """Load data from JSON file with error handling"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.warning(f"⚠️ {filename} not found. Using empty database.")
        return default_data or {}
    except json.JSONDecodeError as e:
        st.error(f"❌ Error reading {filename}: {e}. Using empty database.")
        return default_data or {}
    except Exception as e:
        st.error(f"❌ Unexpected error reading {filename}: {e}. Using empty database.")
        return default_data or {}

# Load vendor and end user databases
VENDOR_DATABASE = load_json_data('vendor.json')
END_USER_DATABASE = load_json_data('endusers.json')

# Sales Person Mapping - GENERIC
SALES_PERSON_MAPPING = {
    "SP1": {"name": "Sales Person 1", "email": "sales1@company.com", "mobile": "+91 00000 00000"},
    "SP2": {"name": "Sales Person 2", "email": "sales2@company.com", "mobile": "+91 00000 00000"},
    "SP3": {"name": "Sales Person 3", "email": "sales3@company.com", "mobile": "+91 00000 00000"},
    "SP4": {"name": "Sales Person 4", "email": "sales4@company.com", "mobile": "+91 00000 00000"}
}

# --- Helper Functions for Vendor Management ---
def get_vendor_dropdown_options():
    """Get vendor names for dropdown"""
    return ["Select Vendor"] + list(VENDOR_DATABASE.keys())

def update_vendor_fields(selected_vendor):
    """Update session state with vendor details when vendor is selected"""
    if selected_vendor and selected_vendor != "Select Vendor":
        vendor_data = VENDOR_DATABASE.get(selected_vendor, {})
        st.session_state.po_vendor_name = selected_vendor
        st.session_state.po_vendor_address = vendor_data.get("address", "")
        st.session_state.po_vendor_contact = vendor_data.get("contact", "")
        st.session_state.po_vendor_mobile = vendor_data.get("mobile", "")
        st.session_state.po_gst_no = vendor_data.get("gst_no", "")
        st.session_state.po_pan_no = vendor_data.get("pan_no", "")
        st.session_state.po_msme_no = vendor_data.get("msme_no", "")

# --- Helper Functions for End User Management ---
def get_enduser_dropdown_options():
    """Get end user names for dropdown"""
    return ["Select End User"] + list(END_USER_DATABASE.keys())

def update_enduser_fields(selected_enduser):
    """Update session state with end user details when end user is selected"""
    if selected_enduser and selected_enduser != "Select End User":
        enduser_data = END_USER_DATABASE.get(selected_enduser, {})
        st.session_state.po_end_company = selected_enduser
        st.session_state.po_end_address = enduser_data.get("address", "")
        st.session_state.po_end_person = enduser_data.get("contact", "")
        st.session_state.po_end_mobile = enduser_data.get("mobile", "")
        st.session_state.po_end_email = enduser_data.get("email", "")
        st.session_state.po_end_gst_no = enduser_data.get("gst_no", "")

# --- Helper Functions for Quotation and PO ---
def get_current_quarter():
    """Get current quarter (Q1, Q2, Q3, Q4) based on current month"""
    month = datetime.datetime.now().month
    if month in [4, 5, 6]:
        return "Q1"
    elif month in [7, 8, 9]:
        return "Q2"
    elif month in [10, 11, 12]:
        return "Q3"
    else:
        return "Q4"

import os

# Simple file-based counter for PO sequence
PO_COUNTER_FILE = "po_counter.txt"

def get_next_po_sequence():
    """Simple file-based PO sequence counter"""
    try:
        if os.path.exists(PO_COUNTER_FILE):
            with open(PO_COUNTER_FILE, 'r') as f:
                current = int(f.read().strip())
        else:
            current = 0
    except:
        current = 0
    
    next_seq = current + 1
    
    with open(PO_COUNTER_FILE, 'w') as f:
        f.write(str(next_seq))
    
    return next_seq

def get_current_po_sequence():
    """Get current PO sequence without incrementing"""
    try:
        if os.path.exists(PO_COUNTER_FILE):
            with open(PO_COUNTER_FILE, 'r') as f:
                return int(f.read().strip())
    except:
        pass
    return 1

def parse_po_number(po_number):
    """Parse PO number to extract components"""
    try:
        parts = po_number.split('/')
        if len(parts) >= 4:
            prefix = parts[0]
            sales_person = parts[1]
            year = parts[2]
            quarter_sequence = parts[3]
            quarter = quarter_sequence.split('_')[0]
            sequence = quarter_sequence.split('_')[1] if '_' in quarter_sequence else "001"
            return prefix, sales_person, year, quarter, sequence
    except:
        pass
    return "COM", "SP1", str(datetime.datetime.now().year), get_current_quarter(), "001"

def generate_po_number(sales_person, sequence_number):
    """Generate PO number with current quarter and sequence"""
    current_date = datetime.datetime.now()
    quarter = get_current_quarter()
    year = str(current_date.year)
    sequence = f"{sequence_number:03d}"
    
    return f"COM/{sales_person}/{year}/{quarter}_{sequence}"

def get_next_sequence_number_po(po_number):
    """Extract and increment sequence number from PO number"""
    try:
        parts = po_number.split('_')
        if len(parts) > 1:
            sequence = parts[-1]
            return int(sequence) + 1
    except:
        pass
    return 1

# Simple file-based counter for quotations
QUOTATION_COUNTER_FILE = "quotation_counter.txt"

def get_next_quotation_sequence():
    """Simple file-based sequence counter"""
    try:
        if os.path.exists(QUOTATION_COUNTER_FILE):
            with open(QUOTATION_COUNTER_FILE, 'r') as f:
                current = int(f.read().strip())
        else:
            current = 0
    except:
        current = 0
    
    next_seq = current + 1
    
    with open(QUOTATION_COUNTER_FILE, 'w') as f:
        f.write(str(next_seq))
    
    return next_seq

def get_current_quotation_sequence():
    """Get current sequence without incrementing"""
    try:
        if os.path.exists(QUOTATION_COUNTER_FILE):
            with open(QUOTATION_COUNTER_FILE, 'r') as f:
                return int(f.read().strip())
    except:
        pass
    return 1

def parse_quotation_number(quotation_number):
    """Parse quotation number to extract components"""
    try:
        parts = quotation_number.split('/')
        if len(parts) >= 5:
            prefix = parts[0]
            sales_person = parts[1]
            quarter = parts[2]
            date_part = parts[3]
            year_range = parts[4].split('_')[0]
            sequence = parts[4].split('_')[1] if '_' in parts[4] else "001"
            return prefix, sales_person, quarter, date_part, year_range, sequence
    except:
        pass
    return "COM", "SP1", get_current_quarter(), datetime.datetime.now().strftime("%d-%m-%Y"), f"{datetime.datetime.now().year}-{datetime.datetime.now().year+1}", "001"

def generate_quotation_number(sales_person, sequence_number):
    """Generate quotation number with current quarter and sequence"""
    current_date = datetime.datetime.now()
    quarter = get_current_quarter()
    year_range = f"{current_date.year}-{current_date.year+1}"
    sequence = f"{sequence_number:03d}"
    
    return f"COM/{sales_person}/{quarter}/{current_date.strftime('%d-%m-%Y')}/{year_range}_{sequence}"

def calculate_quotation_totals(products):
    """Calculate quotation totals with round-off like PO generator"""
    products_total = 0
    for p in products:
        gst_amt = p["basic"] * p["gst_percent"] / 100
        per_unit_price = p["basic"] + gst_amt
        total = per_unit_price * p["qty"]
        products_total += total

    rounded_total = round(products_total)
    round_off = rounded_total - products_total
    
    return {
        "total_base": sum(p["basic"] * p["qty"] for p in products),
        "total_gst": sum(p["basic"] * p["gst_percent"] / 100 * p["qty"] for p in products),
        "grand_total_unrounded": products_total,
        "grand_total": rounded_total,
        "round_off": round_off
    }

def get_next_sequence_number(quotation_number):
    """Extract and increment sequence number from quotation number"""
    try:
        parts = quotation_number.split('_')
        if len(parts) > 1:
            sequence = parts[-1]
            return int(sequence) + 1
    except:
        pass
    return 1

# Simple file-based counter for Invoice sequence
INVOICE_COUNTER_FILE = "invoice_counter.txt"

def get_next_invoice_sequence():
    """Simple file-based Invoice sequence counter"""
    try:
        if os.path.exists(INVOICE_COUNTER_FILE):
            with open(INVOICE_COUNTER_FILE, 'r') as f:
                current = int(f.read().strip())
        else:
            current = 0
    except:
        current = 0
    
    next_seq = current + 1
    
    with open(INVOICE_COUNTER_FILE, 'w') as f:
        f.write(str(next_seq))
    
    return next_seq

def get_current_invoice_sequence():
    """Get current Invoice sequence without incrementing"""
    try:
        if os.path.exists(INVOICE_COUNTER_FILE):
            with open(INVOICE_COUNTER_FILE, 'r') as f:
                return int(f.read().strip())
    except:
        pass
    return 1

def parse_invoice_number(invoice_number):
    """Parse invoice number to extract components"""
    try:
        parts = invoice_number.split('/')
        if len(parts) >= 4:
            prefix = parts[0]
            year_range = parts[1]
            quarter = parts[2]
            sequence = parts[3]
            return prefix, year_range, quarter, sequence
    except:
        pass
    return "COM", f"{str(datetime.datetime.now().year)[2:]}-{str(datetime.datetime.now().year + 1)[2:]}", get_current_quarter(), "01"

def generate_invoice_number(sequence_number):
    """Generate invoice number"""
    current_date = datetime.datetime.now()
    quarter = get_current_quarter()
    year_range = f"{str(current_date.year)[2:]}-{str(current_date.year + 1)[2:]}"
    sequence = f"{sequence_number:02d}"
    
    return f"COM/{year_range}/{quarter}/{sequence}"

def get_next_sequence_number_invoice(invoice_number):
    """Extract and increment sequence number from invoice number"""
    try:
        parts = invoice_number.split('/')
        if len(parts) >= 4:
            sequence = parts[3]
            return int(sequence) + 1
    except:
        pass
    return get_next_invoice_sequence()

# --- PDF Class for Two-Page Quotation ---
class QUOTATION_PDF(FPDF):
    def __init__(self, quotation_number="Q-N/A", quotation_date="Date N/A", sales_person_code="SP1"):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        self.set_left_margin(15)
        self.set_right_margin(15)
        self.quotation_number = quotation_number
        self.quotation_date = quotation_date
        self.sales_person_code = sales_person_code
        font_dir = os.path.join(os.path.dirname(__file__), "fonts")
        try:
            self.add_font("Calibri", "", os.path.join(font_dir, "calibri.ttf"), uni=True)
            self.add_font("Calibri", "B", os.path.join(font_dir, "calibrib.ttf"), uni=True)
            self.add_font("Calibri", "I", os.path.join(font_dir, "calibrii.ttf"), uni=True)
            self.add_font("Calibri", "BI", os.path.join(font_dir, "calibriz.ttf"), uni=True)
            self.default_font = "Calibri"
        except:
            self.default_font = "Helvetica"
        
    def sanitize_text(self, text):
        try:
            return text.encode('latin-1', 'ignore').decode('latin-1')
        except:
            return text

    def header(self):
        if hasattr(self, 'logo_path') and self.logo_path and os.path.exists(self.logo_path):
            try:
                self.image(self.logo_path, x=155, y=8, w=50)
            except:
                self.set_font(self.default_font, "B", 10)
                self.set_xy(150, 8)
                self.cell(40, 5, "[LOGO]", border=0, align="C")
            
        self.set_font(self.default_font, "B", 16)
        self.set_y(15)
        self.ln(5)

    def footer(self):
        self.set_y(-12)
        
        self.set_font("Helvetica", "", 10)
        self.cell(0, 4, "[Company Address Placeholder]", ln=True, align="C")
        
        self.set_font("Helvetica", "U", 10)
        self.set_text_color(0, 0, 255)
        
        email1 = "info@yourcompany.com"
        phone_number = "+91 00000 00000"
        website = "www.yourcompany.com"
        
        contact_text = f"{email1} | {phone_number} | {website}"
        contact_width = self.get_string_width(contact_text)
        x_contact = (self.w - contact_width) / 2
        
        self.set_x(x_contact)
        self.cell(self.get_string_width(email1), 4, email1, link=f"mailto:{email1}")
        self.set_x(x_contact + self.get_string_width(email1) + self.get_string_width(" | "))
        self.cell(self.get_string_width(phone_number), 4, phone_number, link=f"tel:{phone_number}")
        self.set_x(x_contact + self.get_string_width(email1) + self.get_string_width(" | ") + self.get_string_width(phone_number) + self.get_string_width(" | "))
        self.cell(self.get_string_width(website), 4, website, link="https://www.yourcompany.com/")
        
        self.set_text_color(0, 0, 0)

def add_clickable_email(pdf, email, label="Email: "):
    pdf.set_font(pdf.default_font, "B", 12)
    label_width = pdf.get_string_width(label)
    pdf.cell(label_width, 4, label, ln=0)
    
    pdf.set_text_color(0, 0, 255)
    pdf.set_font(pdf.default_font, "", 12)
    pdf.cell(0, 4, email, ln=True, link=f"mailto:{email}")
    pdf.set_text_color(0, 0, 0)

def add_clickable_phone(pdf, phone, label="Mobile: "):
    pdf.set_font(pdf.default_font, "B", 12)
    label_width = pdf.get_string_width(label)
    pdf.cell(label_width, 4, label, ln=0)
    
    pdf.set_text_color(0, 0, 255)
    pdf.set_font(pdf.default_font, "", 12)
    tel_number = phone.replace(' ', '').replace('+', '')
    pdf.cell(0, 4, phone, ln=True, link=f"tel:{tel_number}")
    pdf.set_text_color(0, 0, 0)

def add_page_one_intro(pdf, data):
    pdf.set_font(pdf.default_font, "B", 12)
    pdf.set_y(35)
    pdf.cell(0, 5, f"REF NO.: {data['quotation_number']}", ln=True, align="L")
    pdf.cell(0, 5, f"Date: {data['quotation_date']}", ln=True, align="L")
    pdf.ln(5)

    pdf.set_font(pdf.default_font, "", 12)
    pdf.cell(0, 5, "To,", ln=True)
    pdf.set_font(pdf.default_font, "B", 12)
    pdf.cell(0, 6, pdf.sanitize_text(data['vendor_name']), ln=True)
    pdf.set_font(pdf.default_font, "", 12)
    
    pdf.multi_cell(94, 4, pdf.sanitize_text(data['vendor_address']))
    
    pdf.ln(3)
    
    if data.get('vendor_email'):
        add_clickable_email(pdf, data['vendor_email'])
        
    pdf.ln(1)
    if data.get('vendor_mobile'):
        add_clickable_phone(pdf, data['vendor_mobile'])
    
    pdf.set_font(pdf.default_font, "BU", 12)
    pdf.cell(0, 5, f"Kind Attention :- {pdf.sanitize_text(data['vendor_contact'])}", align="C", ln=True)
    pdf.ln(5)

    pdf.set_font(pdf.default_font, "BU", 12)
    pdf.cell(0, 6, f"Subject :- {pdf.sanitize_text(data['subject'])}", ln=True)
    pdf.ln(8)

    intro_text = pdf.sanitize_text(data.get("intro_paragraph", ""))
    if intro_text:
        write_simple_justified_paragraph(pdf, intro_text)

    fixed_paragraphs = [
        "Enclosed please find our Quotation for your information and necessary action.",
        "[Company Introduction Paragraph 1]",
        "[Company Introduction Paragraph 2]",
        "[Company Introduction Paragraph 3]"
    ]

    for paragraph in fixed_paragraphs:
        write_simple_justified_paragraph(pdf, paragraph)
        pdf.ln(3)

    if pdf.get_y() > 220:
        pdf.add_page()
    
    pdf.set_font(pdf.default_font, "", 12)
    pdf.set_text_color(0, 0, 0)

    contact_text = "Please revert back to us, if you need any clarification / information at the below mentioned address or email at "
    pdf.write(5, contact_text)

    sales_person_code = data.get('sales_person_code', 'SP1')
    sales_person_info = SALES_PERSON_MAPPING.get(sales_person_code, SALES_PERSON_MAPPING['SP1'])
    
    pdf.set_text_color(0, 0, 255)
    pdf.set_font(pdf.default_font, "U", 12)
    pdf.write(5, sales_person_info["email"], link=f"mailto:{sales_person_info['email']}")

    pdf.set_text_color(0, 0, 0)
    pdf.set_font(pdf.default_font, "", 12)
    pdf.write(5, "  Mobile: ")

    pdf.set_text_color(0, 0, 255)
    pdf.set_font(pdf.default_font, "U", 12)
    pdf.write(5, sales_person_info["mobile"], link=f"tel:{sales_person_info['mobile'].replace(' ', '').replace('+', '')}")

    pdf.ln(10)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font(pdf.default_font, "", 12)
    pdf.cell(0, 4, "For more information, please visit our web site & Social Media :-", ln=True)
    pdf.set_font(pdf.default_font, "", 12)
    
    pdf.set_font(pdf.default_font, "U", 12)
    pdf.set_text_color(0, 0, 255)

    links = [
        "https://www.yourcompany.com/",
        "https://www.linkedin.com/company/yourcompany", 
        "https://wa.me/910000000000",
        "https://www.facebook.com/yourcompany",
        "https://www.instagram.com/yourcompany"
    ]

    max_link_width = max(pdf.get_string_width(link) for link in links)
    right_margin = pdf.w - pdf.r_margin

    for link in links:
        x_position = right_margin - max_link_width
        pdf.set_x(x_position)
        pdf.cell(max_link_width, 4, link, ln=True, link=link)

    pdf.set_text_color(0, 0, 0)

def write_simple_justified_paragraph(pdf, text):
    pdf.set_font(pdf.default_font, "", 12)
    pdf.set_text_color(0, 0, 0)
    
    paragraphs = text.split('\n')
    
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if paragraph:
            pdf.multi_cell(0, 5, paragraph, align='J')
            pdf.ln(3)

def add_quotation_header(pdf, annexure_text, quotation_text):
    pdf.set_font(pdf.default_font, "BU", 14)
    pdf.cell(0, 8, annexure_text, ln=True, align="C")
    pdf.set_font(pdf.default_font, "BU", 12)
    pdf.cell(0, 6, quotation_text, ln=True, align="C")
    pdf.ln(8)

def add_page_two_commercials(pdf, data):
    pdf.add_page()
    pdf.ln(10)
    
    annexure_text = data.get('annexure_text', 'Annexure I - Commercials')
    quotation_title = data.get('quotation_title', 'Quotation for Software Services')
    
    add_quotation_header(pdf, annexure_text, quotation_title)

    col_widths = [70, 25, 25, 25, 15, 25]
    headers = ["Description", "Basic Price", "GST Tax @ 18%", "Per Unit Price", "Qty.", "Total"]
    
    pdf.set_fill_color(220, 220, 220)
    pdf.set_font(pdf.default_font, "B", 10)
    for width, header in zip(col_widths, headers):
        pdf.cell(width, 6, header, border=1, align="C", fill=True)
    pdf.ln()
    
    pdf.set_font(pdf.default_font, "", 12)
    grand_total_unrounded = 0.0
    
    for product in data["products"]:
        basic_price = product["basic"]
        qty = product["qty"]
        gst_amount = basic_price * (product.get("gst_percent", 18.0) / 100)
        per_unit_price = basic_price + gst_amount
        total = per_unit_price * qty
        grand_total_unrounded += total
        
        start_y = pdf.get_y()
        
        desc = product["name"]
        pdf.set_font(pdf.default_font, "", 10)
        
        desc_lines = pdf.multi_cell(col_widths[0], 5, desc, border=0, split_only=True)
        desc_height = len(desc_lines) * 6
        
        pdf.set_xy(pdf.l_margin, start_y)
        
        if len(desc_lines) > 1:
            pdf.multi_cell(col_widths[0], 6, desc, border=1)
            current_y = pdf.get_y()
            
            pdf.set_xy(pdf.l_margin + col_widths[0], start_y)
            pdf.cell(col_widths[1], desc_height, f"{basic_price:,.2f}", border=1, align="R")
            pdf.cell(col_widths[2], desc_height, f"{gst_amount:,.2f}", border=1, align="R")
            pdf.cell(col_widths[3], desc_height, f"{per_unit_price:,.2f}", border=1, align="R")
            pdf.cell(col_widths[4], desc_height, f"{qty:.0f}", border=1, align="C")
            pdf.cell(col_widths[5], desc_height, f"{total:,.2f}", border=1, align="R")
            
            pdf.set_y(current_y)
        else:
            pdf.cell(col_widths[0], 6, desc, border=1)
            pdf.cell(col_widths[1], 6, f"{basic_price:,.2f}", border=1, align="R")
            pdf.cell(col_widths[2], 6, f"{gst_amount:,.2f}", border=1, align="R")
            pdf.cell(col_widths[3], 6, f"{per_unit_price:,.2f}", border=1, align="R")
            pdf.cell(col_widths[4], 6, f"{qty:.0f}", border=1, align="C")
            pdf.cell(col_widths[5], 6, f"{total:,.2f}", border=1, align="R")
            pdf.ln()

    round_off = data.get('round_off', 0.0)
    pdf.set_font(pdf.default_font, "B", 10)
    pdf.cell(sum(col_widths[:-1]), 7, "Round Off", border=1, align="R")
    pdf.cell(col_widths[5], 7, f"{round_off:,.2f}", border=1, align="R")
    pdf.ln()

    grand_total = data.get('grand_total', grand_total_unrounded)
    pdf.set_font(pdf.default_font, "B", 10)
    pdf.cell(sum(col_widths[:-1]), 7, "Final Amount to be Paid", border=1, align="R")
    pdf.cell(col_widths[5], 7, f"{grand_total:,.2f}", border=1, align="R")
    pdf.ln(15)

    pdf.set_font(pdf.default_font, "", 9)

    price_validity = data.get('price_validity', '10 days from Quotation date')
    terms = [
        ("1. Above charges are Inclusive of GST.", ""),
        ("2. Any changes in Govt. duties, Taxes & Forex rate at the time of dispatch shall be applicable.", ""),
        ("3. TDS should not be deducted at the time of payment as per Govt. regulations.", ""),
        ("4. Software licenses are delivered electronically.", ""),
        ("5. An Internet connection is required to access cloud services.", ""),
        ("6. Training will be charged at extra cost depending on no. of participants.", ""),
        ("7. Price Validity: ", price_validity),
        ("8. Payment: ", "100% Advance along with purchase order"),
        ("9. Delivery period: ", "1-2 Weeks from the date of Purchase Order"),
        ("10. Support: ","Includes 12 months of technical support and software updates."),
        ("11. Installation: ","Online"),
        ("12. Cheque to be issued on name of: ", '"[Your Company Name]"'),
        ("13. Order to be placed on: ", "[Your Company Name] \n[Your Company Address]")
    ]

    bank_info = [
        ("Name", "[Your Company Name]"),
        ("Account Number", "[Your Account Number]"),
        ("IFSC Code", "[Your IFSC Code]"),
        ("SWIFT Code", "[Your SWIFT Code]"),
        ("Bank Name", "[Your Bank Name]"),
        ("Branch", "[Your Branch Name]"),
        ("MSME", "[Your MSME Number]"),
        ("GSTIN", "[Your GSTIN]"),
        ("PAN No", "[Your PAN Number]")
    ]

    x_start = pdf.get_x()
    y_start = pdf.get_y()
    page_width = pdf.w - 1.6 * pdf.l_margin
    col1_width = page_width * 0.62
    col2_width = page_width * 0.38
    padding = 2.5
    line_height = 4
    section_spacing = 2

    def calculate_column_height(items, col_width):
        height = 0
        for label, value in items:
            if value:
                text = f"{label}{value}"
            else:
                text = label
            lines = pdf.multi_cell(col_width - 2*padding, line_height, text, split_only=True)
            height += len(lines) * line_height + section_spacing
        return height + 3*padding

    terms_height = calculate_column_height(terms, col1_width)
    bank_items_height = calculate_column_height(bank_info, col2_width)
    signature_height = 35
    
    box_height = max(terms_height, bank_items_height + signature_height)

    pdf.rect(x_start, y_start, page_width, box_height)
    pdf.line(x_start + col1_width, y_start, x_start + col1_width, y_start + box_height)

    pdf.set_font(pdf.default_font, "B", 12)
    pdf.set_xy(x_start + padding, y_start + padding)
    pdf.cell(col1_width - 2*padding, 5, "Terms & Conditions:", ln=True)

    terms_y = pdf.get_y()
    for i, (label, value) in enumerate(terms):
        pdf.set_xy(x_start + padding, terms_y)
        
        if i < 6:
            pdf.set_font(pdf.default_font, "B", 10)
            pdf.multi_cell(col1_width - 2*padding, line_height, label)
            
        elif value:
            pdf.set_font(pdf.default_font, "", 10)
            pdf.cell(pdf.get_string_width(label), line_height, label, ln=0)
            
            pdf.set_font(pdf.default_font, "B", 10)
            remaining_width = col1_width - 2*padding - pdf.get_string_width(label)
            pdf.multi_cell(remaining_width, line_height, value)
            
            pdf.set_font(pdf.default_font, "", 10)
        else:
            pdf.multi_cell(col1_width - 2*padding, line_height, label)
        
        terms_y = pdf.get_y()

    pdf.set_font(pdf.default_font, "B", 12)
    pdf.set_xy(x_start + col1_width + padding, y_start + padding)
    pdf.cell(col2_width - 2*padding, 5, "Bank Details:", ln=True)
    pdf.set_font(pdf.default_font, "", 12)

    bank_y = pdf.get_y()
    for label, value in bank_info:
        pdf.set_xy(x_start + col1_width + padding, bank_y)
        
        pdf.set_font(pdf.default_font, "", 10)
        pdf.cell(pdf.get_string_width(f"{label}: "), line_height, f"{label}: ", ln=0)
        
        pdf.set_font(pdf.default_font, "B", 10)
        remaining_width = col2_width - 2*padding - pdf.get_string_width(f"{label}: ")
        pdf.multi_cell(remaining_width, line_height, value)
        
        bank_y = pdf.get_y()

    signature_start_y = y_start + box_height - signature_height - 15
    
    pdf.set_font(pdf.default_font, "B", 10)
    pdf.set_xy(x_start + col1_width + padding, signature_start_y)
    pdf.cell(col2_width - 2*padding, 5, "Yours Truly,", ln=True)
    
    pdf.set_xy(x_start + col1_width + padding, pdf.get_y())
    pdf.cell(col2_width - 2*padding, 5, "For [Your Company Name]", ln=True)
    
    sales_person_code = data.get('sales_person_code', 'SP1')
    sales_person_info = SALES_PERSON_MAPPING.get(sales_person_code, SALES_PERSON_MAPPING['SP1'])
    
    if data.get('stamp_path') and os.path.exists(data['stamp_path']):
        try:
            stamp_y = pdf.get_y() + 2
            stamp_x = x_start + col1_width + padding
            pdf.image(data['stamp_path'], x=stamp_x, y=stamp_y, w=20)
            pdf.set_y(stamp_y + 20)
        except:
            pdf.set_y(pdf.get_y() + 8)
    else:
        pdf.set_y(pdf.get_y() + 8)
    
    pdf.set_font(pdf.default_font, "", 9)
    pdf.set_xy(x_start + col1_width + padding, pdf.get_y())
    pdf.cell(col2_width - 2*padding, 4, sales_person_info["name"], ln=True)
    
    pdf.set_xy(x_start + col1_width + padding, pdf.get_y())
    pdf.cell(col2_width - 2*padding, 4, "Sales Executive", ln=True)
    
    pdf.set_font(pdf.default_font, "", 9)
    pdf.set_text_color(0, 0, 0)
    pdf.set_xy(x_start + col1_width + padding, pdf.get_y())
    label = "Email: "
    pdf.cell(pdf.get_string_width(label), 4, label, ln=0)
    pdf.set_font(pdf.default_font, "U", 9)
    pdf.set_text_color(0, 0, 255)
    pdf.cell(col2_width - 2*padding - pdf.get_string_width(label), 4, sales_person_info["email"], 
             ln=True, link=f"mailto:{sales_person_info['email']}")
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font(pdf.default_font, "", 9)
    pdf.set_xy(x_start + col1_width + padding, pdf.get_y())
    label = "Mobile: "
    pdf.cell(pdf.get_string_width(label), 4, label, ln=0)
    pdf.set_font(pdf.default_font, "U", 9)
    pdf.set_text_color(0, 0, 255)
    pdf.cell(col2_width - 2*padding - pdf.get_string_width(label), 4, sales_person_info["mobile"], 
             ln=True, link=f"tel:{sales_person_info['mobile'].replace(' ', '').replace('+', '')}")
    pdf.set_text_color(0, 0, 0)

    pdf.set_xy(x_start, y_start + box_height + 10)
    
def create_quotation_pdf(quotation_data, logo_path=None, stamp_path=None):
    sales_person_code = quotation_data.get('sales_person_code', 'SP1')
    pdf = QUOTATION_PDF(quotation_number=quotation_data['quotation_number'], 
                        quotation_date=quotation_data['quotation_date'],
                        sales_person_code=sales_person_code)
    
    if logo_path and os.path.exists(logo_path):
        pdf.logo_path = logo_path
    
    quotation_data['stamp_path'] = stamp_path

    pdf.add_page()
    
    add_page_one_intro(pdf, quotation_data)
    add_page_two_commercials(pdf, quotation_data)
    
    try:
        pdf_output = pdf.output(dest='S')
        
        if isinstance(pdf_output, str):
            return pdf_output.encode('latin-1')
        elif isinstance(pdf_output, bytearray):
            return bytes(pdf_output)
        elif isinstance(ppdf_output, bytes):
            return pdf_output
        else:
            return str(pdf_output).encode('latin-1')
            
    except Exception:
        try:
            buffer = io.BytesIO()
            pdf.output(dest=buffer)
            return buffer.getvalue()
        except Exception as e:
            st.error(f"PDF generation failed: {e}")
            return b""

from fpdf import FPDF
# --- PDF Class for Tax Invoice ---
class PDF(FPDF):
    def __init__(self):
        super().__init__()
        
        font_dir = os.path.join(os.path.dirname(__file__), "fonts")
        try:
            self.add_font("Calibri", "", os.path.join(font_dir, "calibri.ttf"), uni=True)
            self.add_font("Calibri", "B", os.path.join(font_dir, "calibrib.ttf"), uni=True)
            self.add_font("Calibri", "I", os.path.join(font_dir, "calibrii.ttf"), uni=True)
            self.add_font("Calibri", "BI", os.path.join(font_dir, "calibriz.ttf"), uni=True)
            self.default_font = "Calibri"
        except:
            self.default_font = "Helvetica"

        self.set_font(self.default_font, "", 8)
        self.set_left_margin(10)
        self.set_right_margin(15)
        
        self.logo_file = None

    def header(self):
        if self.logo_file and self.page_no() >= 1:
            try:
                self.image(self.logo_file, x=155, y=8, w=50)
            except Exception as e:
                pass
        self.ln(9)
        self.set_font(self.default_font, "B", 15)
        self.cell(0, 6, "TAX INVOICE", ln=True, align="C")
        self.ln(1)
        
    def footer(self):
        self.set_y(-15)
        
        self.set_font(self.default_font, "I", 10)
        self.cell(0, 4, "This is a Computer Generated Invoice", ln=True, align="C")
        
        self.set_font(self.default_font, "", 10)
        self.cell(0, 4, "[Your Company Address]", ln=True, align="C")
        
        self.set_font(self.default_font, "U", 10)
        self.set_text_color(0, 0, 255)
        
        email1 = "info@yourcompany.com"
        phone_number = "+91 00000 00000"
        website = "www.yourcompany.com"
        
        contact_text = f"{email1} | {phone_number} | {website}"
        contact_width = self.get_string_width(contact_text)
        x_contact = (self.w - contact_width) / 2
        
        self.set_x(x_contact)
        self.cell(self.get_string_width(email1), 4, email1, link=f"mailto:{email1}")
        self.set_x(x_contact + self.get_string_width(email1) + self.get_string_width(" | "))
        self.cell(self.get_string_width(phone_number), 4, phone_number, link=f"tel:{phone_number}")
        self.set_x(x_contact + self.get_string_width(email1) + self.get_string_width(" | ") + self.get_string_width(phone_number) + self.get_string_width(" | "))
        self.cell(self.get_string_width(website), 4, website, link="https://www.yourcompany.com/")
        
        self.set_text_color(0, 0, 0)

# --- Function to Create Invoice PDF ---
def create_invoice_pdf(invoice_data, logo_file=None, stamp_file=None):
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=10)
    
    pdf.logo_file = logo_file
    
    pdf.add_page()

    pdf.set_font(pdf.default_font, "B", 13)
    pdf.cell(95, 8, "[Your Company Name].", border="LRT", ln=0)
    pdf.cell(48, 8, "Invoice No.", border=1, ln=0, align="L")
    pdf.cell(48, 8, "Invoice Date", border=1, ln=1, align="L")

    y_left_start = pdf.get_y()

    pdf.set_font(pdf.default_font, "", 12)
    pdf.multi_cell(95, 4, invoice_data['vendor']['address'], border="L")
    
    vendor_lines = [
        ("GST No. : ", invoice_data['vendor']['gst']),
        ("MSME Registration No. : ", invoice_data['vendor']['msme']),
        ("E-Mail : ", "info@yourcompany.com"),
        ("Mobile No. : ", "0000000000"),
    ]
    
    for i, (label, value) in enumerate(vendor_lines):
        pdf.set_x(10)
        pdf.set_font(pdf.default_font, "B", 12)
        label_width = pdf.get_string_width(label) 
        pdf.cell(label_width, 6, label, border="L", ln=0)
        pdf.set_font(pdf.default_font, "", 12)
        border = "R" if i < len(vendor_lines) - 1 else "R"
        pdf.cell(95 - label_width, 6, value, border=border, ln=1)

    y_left_end = pdf.get_y()

    pdf.set_xy(105, y_left_start)
    pdf.set_font(pdf.default_font, "", 12)
    pdf.cell(48, 8, invoice_data['invoice']['invoice_no'], border="LR", ln=0, align="L")
    pdf.cell(48, 8, invoice_data['invoice']['date'], border="R", ln=1, align="L")

    payment_terms = invoice_data['invoice_details'].get('payment_terms', '100% Advance with Purchase')

    y_before = pdf.get_y()
    pdf.set_xy(153, y_before)
    pdf.multi_cell(48, 4, payment_terms, border="LRT", align="L")

    y_after = pdf.get_y()
    actual_height = y_after - y_before

    if actual_height < 8:
        remaining_height = 8 - actual_height
        pdf.set_xy(153, y_after)
        pdf.cell(48, remaining_height, "", border="LR", ln=True)

    pdf.set_x(105)
    pdf.set_font(pdf.default_font, "B", 12)
    pdf.cell(48, 8, "Supplier's Reference:", border="LRT", ln=0)
    pdf.set_font(pdf.default_font, "", 12)
    other_ref_value = invoice_data['Reference']['Suppliers_Reference']
    pdf.cell(48, 8, other_ref_value, border="LRTB", ln=1)

    pdf.set_x(105)
    pdf.set_font(pdf.default_font, "B", 12)
    pdf.cell(48, 8, "Other's Reference:", border="LRTB", ln=0)
    pdf.set_font(pdf.default_font, "", 12)
    other_ref_value = invoice_data['Reference']['Other']
    pdf.cell(48, 8, other_ref_value, border="LRTB", ln=1)

    pdf.set_font(pdf.default_font, "B", 12)
    pdf.cell(95, 6, "Buyer", border="LT", ln=0)
    pdf.cell(48, 6, "Buyer's Order No.", border=1, ln=0, align="L")
    pdf.cell(48, 6, "Buyer's Order Date", border=1, ln=1, align="L")

    y_buyer_start = pdf.get_y()

    y_left_buyer_start = pdf.get_y()
    
    pdf.set_font(pdf.default_font, "B", 12)
    pdf.multi_cell(95, 5, invoice_data['buyer']['name'], border="LR")
    
    pdf.set_font(pdf.default_font, "", 12)
    pdf.multi_cell(95, 4, invoice_data['buyer']['address'], border="LR")
    
    buyer_lines = [
        ("Email :", invoice_data['buyer']['email']),
        ("Mobile No :", invoice_data['buyer']['mobile']),
        ("GST No. :", invoice_data['buyer']['gst']),
    ]
    
    for i, (label, value) in enumerate(buyer_lines):
        pdf.set_x(10)
        pdf.set_font(pdf.default_font, "B", 12)
        label_width = pdf.get_string_width(label) + 1
        pdf.cell(label_width, 6, label, border="L", ln=0)
        pdf.set_font(pdf.default_font, "", 12)
        border = "R" if i < len(buyer_lines) - 1 else "R"
        pdf.cell(95 - label_width, 6, value, border=border, ln=1)

    y_buyer_left_end = pdf.get_y()
    total_left_height = y_buyer_left_end - y_left_buyer_start

    pdf.set_xy(105, y_buyer_start)
    
    num_right_rows = 4
    right_cell_height = total_left_height / num_right_rows
    
    pdf.set_font(pdf.default_font, "", 12)
    pdf.cell(48, right_cell_height, invoice_data['invoice_details']['buyers_order_no'], border="LR", ln=0, align="L")
    pdf.cell(48, right_cell_height, invoice_data['invoice_details']['buyers_order_date'], border="R", ln=1, align="L")

    pdf.set_x(105)
    pdf.set_font(pdf.default_font, "B", 12)
    pdf.cell(48, right_cell_height, "Dispatched Through", border="LRT", ln=0)
    pdf.set_font(pdf.default_font, "", 12)
    pdf.cell(48, right_cell_height, invoice_data['invoice_details']['dispatched_through'], border="RT", ln=1)

    pdf.set_x(105)
    pdf.set_font(pdf.default_font, "B", 12)
    pdf.cell(48, right_cell_height, "Destination", border="LRT", ln=0)
    pdf.set_font(pdf.default_font, "", 12)
    destination = invoice_data['invoice_details'].get('destination', 'City Name')
    pdf.cell(48, right_cell_height, destination, border="RT", ln=1)

    pdf.set_x(105)
    pdf.set_font(pdf.default_font, "B", 12)
    pdf.cell(48, right_cell_height, "Terms of delivery", border="LRT", ln=0)
    pdf.set_font(pdf.default_font, "", 12)
    pdf.cell(48, right_cell_height, invoice_data['invoice_details']['terms_of_delivery'], border="LRT", ln=1)

    pdf.set_y(max(y_buyer_left_end, y_buyer_start + total_left_height))
    
    pdf.ln(0.3)
    
    pdf.set_font(pdf.default_font, "B", 12)
    col_widths = [13, 82, 22, 23, 23, 28]
    
    pdf.cell(col_widths[0], 5, "Sr.No.", border=1, align="C")
    pdf.cell(col_widths[1], 5, "Description of Goods", border=1, align="C")
    pdf.cell(col_widths[2], 5, "HSN/SAC", border=1, align="C")
    pdf.cell(col_widths[3], 5, "Quantity", border=1, align="C")
    pdf.cell(col_widths[4], 5, "Unit Rate", border=1, align="C")
    pdf.cell(col_widths[5], 5, "Amount", border=1, ln=True, align="C")

    pdf.set_font(pdf.default_font, "", 12)
    line_height = 5

    hsn_codes = []
    
    for i, item in enumerate(invoice_data["items"], start=1):
        hsn_codes.append(item['hsn'])
        
        if pdf.get_y() + 25 > pdf.page_break_trigger:
            pdf.add_page()
            pdf.set_font(pdf.default_font, "B", 12)
            pdf.cell(col_widths[0], 5, "Sr. No.", border=1, align="C")
            pdf.cell(col_widths[1], 5, "Description of Goods", border=1, align="C")
            pdf.cell(col_widths[2], 5, "HSN/SAC", border=1, align="C")
            pdf.cell(col_widths[3], 5, "Quantity", border=1, align="C")
            pdf.cell(col_widths[4], 5, "Unit Rate", border=1, align="C")
            pdf.cell(col_widths[5], 5, "Amount", border=1, ln=True, align="C")
            pdf.set_font(pdf.default_font, "", 12)
            
        x_start = pdf.get_x()
        y_start = pdf.get_y()

        pdf.set_xy(x_start + col_widths[0], y_start)
        pdf.multi_cell(col_widths[1], line_height, item['description'], border="LRT", align="L")
        y_after_desc = pdf.get_y()
        
        row_height = y_after_desc - y_start
        
        pdf.set_xy(x_start, y_start)
        pdf.multi_cell(col_widths[0], row_height, str(i), border="LRT", align="C")
        
        pdf.set_xy(x_start + col_widths[0] + col_widths[1], y_start)
        pdf.multi_cell(col_widths[2], row_height, item['hsn'], border="LRT", align="C")
        
        pdf.set_xy(x_start + sum(col_widths[:3]), y_start)
        pdf.multi_cell(col_widths[3], row_height, str(item['quantity']), border="LRT", align="C")
        
        pdf.set_xy(x_start + sum(col_widths[:4]), y_start)
        pdf.multi_cell(col_widths[4], row_height, f"{item['unit_rate']:,.2f}", border="LRT", align="R")
        
        amount = item['quantity'] * item['unit_rate']
        pdf.set_xy(x_start + sum(col_widths[:-1]), y_start)
        pdf.multi_cell(col_widths[5], row_height, f"{amount:,.2f}", border="LRT", align="R")

        pdf.set_xy(x_start, y_start + row_height)

    x_start = pdf.get_x()
    y_start = pdf.get_y()
    
    empty_row_height = 15
    
    pdf.set_xy(x_start, y_start)
    pdf.multi_cell(col_widths[0], empty_row_height, "", border="LRB", align="C")
    
    pdf.set_xy(x_start + col_widths[0], y_start)
    pdf.multi_cell(col_widths[1], empty_row_height, "", border="LRB", align="C")
    
    pdf.set_xy(x_start + col_widths[0] + col_widths[1], y_start)
    pdf.multi_cell(col_widths[2], empty_row_height, "", border="LRB", align="C")
    
    pdf.set_xy(x_start + sum(col_widths[:3]), y_start)
    pdf.multi_cell(col_widths[3], empty_row_height, "", border="LRB", align="C")
    
    pdf.set_xy(x_start + sum(col_widths[:4]), y_start)
    pdf.multi_cell(col_widths[4], empty_row_height, "", border="LRB", align="C")
    
    pdf.set_xy(x_start + sum(col_widths[:-1]), y_start)
    pdf.multi_cell(col_widths[5], empty_row_height, "", border="LRB", align="C")
    
    pdf.set_xy(x_start, y_start + empty_row_height)

    if pdf.get_y() + 60 > pdf.page_break_trigger:
        pdf.add_page()

    pdf.set_font(pdf.default_font, "B", 12)
    total_width = sum(col_widths[:5])
    pdf.ln(0.2)
    pdf.cell(total_width, 5, "Basic Amount", border=1, align="L")
    pdf.cell(col_widths[5], 5, f"{invoice_data['totals']['basic_amount']:,.2f}", border=1, ln=True, align="R")
    
    pdf.cell(total_width, 5, "SGST @ 9%", border=1, align="L")
    pdf.cell(col_widths[5], 5, f"{invoice_data['totals']['sgst']:,.2f}", border=1, ln=True, align="R")
    
    pdf.cell(total_width, 5, "CGST @ 9%", border=1, align="L")
    pdf.cell(col_widths[5], 5, f"{invoice_data['totals']['cgst']:,.2f}", border=1, ln=True, align="R")
    
    round_off = invoice_data['totals']['final_amount'] - (invoice_data['totals']['basic_amount'] + invoice_data['totals']['sgst'] + invoice_data['totals']['cgst'])
    if round_off != 0:
        pdf.cell(total_width, 5, "Round Off", border=1, align="L")
        pdf.cell(col_widths[5], 5, f"{round_off:,.2f}", border=1, ln=True, align="R")

    pdf.cell(total_width, 5, "Final Amount to be Paid", border=1, align="L")
    pdf.cell(col_widths[5], 5, f"{invoice_data['totals']['final_amount']:,.2f}", border=1, ln=True, align="R")
    
    pdf.cell(191, 5, "", border=1, ln=True)

    pdf.set_y(pdf.get_y() - 5)
    pdf.set_x(10)

    pdf.set_font(pdf.default_font, "B", 12)
    pdf.cell(pdf.get_string_width("Amount Chargeable (in words): "), 5, "Amount Chargeable (in words): ", ln=0)

    pdf.set_font(pdf.default_font, "", 12)
    pdf.cell(0, 5, invoice_data['totals']['amount_in_words'], ln=True)

    if pdf.get_y() + 60 > pdf.page_break_trigger:
        pdf.add_page()

    pdf.set_font(pdf.default_font, "B", 12)
    
    pdf.cell(34, 10, "HSN/SAC", border="LRT", align="C")
    pdf.cell(34, 10, "Taxable Value", border="LRT", align="C")
    pdf.cell(60, 5, "Central Tax", border=1, align="C")
    pdf.cell(63, 5, "State Tax", border=1, ln=True, align="C")

    pdf.cell(34, 1, "", border="L", ln=False)
    pdf.cell(34, 1, "", border="L", ln=False)
    pdf.cell(30, 5, "Rate", border="L", align="C")
    pdf.cell(30, 5, "Amount", border="LR", align="C")
    pdf.cell(32, 5, "Rate", border="L", align="C")
    pdf.cell(31, 5, "Amount", border="LR", ln=True, align="C")

    pdf.set_font(pdf.default_font, "", 12)
    
    primary_hsn = hsn_codes[0] if hsn_codes else ""
    
    hsn_tax_value = sum(item['quantity'] * item['unit_rate'] for item in invoice_data["items"])
    hsn_sgst = hsn_tax_value * 0.09
    hsn_cgst = hsn_tax_value * 0.09
    
    pdf.cell(34, 5, primary_hsn, border=1, align="C")
    pdf.cell(34, 5, f"{hsn_tax_value:,.2f}", border=1, align="C")
    pdf.cell(30, 5, "9%", border=1, align="C")
    pdf.cell(30, 5, f"{hsn_sgst:,.2f}", border=1, align="C")
    pdf.cell(32, 5, "9%", border=1, align="C")
    pdf.cell(31, 5, f"{hsn_cgst:,.2f}", border=1, ln=True, align="C")

    pdf.set_font(pdf.default_font, "B", 12)
    pdf.cell(34, 5, "Total", border=1, align="C")
    pdf.cell(34, 5, f"{hsn_tax_value:,.2f}", border=1, align="C")
    pdf.cell(30, 5, "", border=1, align="C")
    pdf.cell(30, 5, f"{hsn_sgst:,.2f}", border=1, align="C")
    pdf.cell(32, 5, "", border=1, align="C")
    pdf.cell(31, 5, f"{hsn_cgst:,.2f}", border=1, ln=True, align="C")
    
    pdf.set_font(pdf.default_font, "B", 12)
    label_part = "Tax Amount (in words): "
    pdf.cell(pdf.get_string_width(label_part), 5, label_part, border="LTB", ln=0)

    pdf.set_font(pdf.default_font, "", 12)
    value_part = invoice_data['totals']['tax_in_words']
    remaining_width = 189.7 - pdf.get_string_width(label_part)
    pdf.cell(remaining_width, 5, value_part, border="TRB", ln=True)

    if pdf.get_y() + 80 > pdf.page_break_trigger:
        pdf.add_page()

    pdf.set_font(pdf.default_font, "B", 10)
    pdf.cell(95, 5, "Company's Bank Details", ln=0, border=1)
    pdf.cell(96, 5, "Declaration:", ln=1, border=1)

    y_before = pdf.get_y()
    x_left = pdf.get_x()

    bank_lines = [
        ("Bank Name", "[Your Bank Name]"),
        ("Branch", "[Your Branch Name]"),
        ("Account No", "[Your Account Number]"),
        ("IFS Code", "[Your IFS Code]")
    ]
    
    pdf.set_font(pdf.default_font, "", 10)
    
    label_start_x = x_left
    colon_x = label_start_x + 25
    value_start_x = colon_x + 5
    
    current_y = y_before
    for label, value in bank_lines:
        pdf.set_xy(label_start_x, current_y)
        pdf.set_font(pdf.default_font, "B", 10)
        pdf.cell(25, 5, label, border="L", ln=0)
        
        pdf.set_xy(colon_x, current_y)
        pdf.cell(5, 5, ":", ln=0)
        
        pdf.set_xy(value_start_x, current_y)
        pdf.set_font(pdf.default_font, "", 10)
        pdf.cell(50, 5, value, border="", ln=1)
        
        current_y += 5
    
    y_after_left = current_y
    
    pdf.set_xy(x_left + 95, y_before)
    pdf.set_font(pdf.default_font, "", 10)
    pdf.multi_cell(96, 4, invoice_data['declaration'], border=1)
    y_after_right = pdf.get_y()
    
    max_y = max(y_after_left, y_after_right)
    pdf.set_y(max_y)

    y_signature_start = pdf.get_y()

    pdf.set_font(pdf.default_font, "B", 10)
    pdf.cell(95, 6, "Buyer's Company Signature", border="LRT", ln=0, align="C")

    pdf.cell(96, 6, "For [Your Company Name].", border="LR", ln=1, align="C")

    left_signature_box_height = 33
    right_signature_box_height = 33

    pdf.set_font(pdf.default_font, "I", 10)
    pdf.set_text_color(128, 128, 128)

    buyer_logo_file = invoice_data.get('buyer', {}).get('logo_file')

    if buyer_logo_file:
        try:
            logo_width = 25
            logo_x = 10 + (95 - logo_width) / 2
            logo_y = pdf.get_y() + 4
            
            pdf.image(buyer_logo_file, x=logo_x, y=logo_y, w=logo_width)
            
            pdf.set_xy(10, logo_y + logo_width + 2)
            pdf.set_font(pdf.default_font, "B", 9)
            pdf.cell(95, 4, invoice_data['buyer']['name'], border=0, ln=1, align="C")
            
            pdf.set_xy(10, pdf.get_y() + 8)
            pdf.set_font(pdf.default_font, "", 9)
            pdf.cell(95, 4, "_________________________", border=0, ln=1, align="C")
            pdf.cell(95, 4, "Authorized Signatory", border=0, ln=1, align="C")
            
            pdf.set_xy(10, y_signature_start + 6)
            pdf.cell(95, left_signature_box_height, "", border="LRB")
            
            y_after_left_signature = y_signature_start + 6 + left_signature_box_height
            
        except Exception as e:
            st.warning(f"Could not add buyer logo: {e}")
            pdf.multi_cell(95, left_signature_box_height/5, "\n\n(Space for Buyer's Company\nStamp and Signature)", border="LRB", align="C")
            y_after_left_signature = pdf.get_y()
    else:
        pdf.multi_cell(95, left_signature_box_height/5, "\n\n\n(Space for Buyer's Company\nStamp and Signature)", border="LRB", align="C")
        y_after_left_signature = pdf.get_y()

    pdf.set_xy(105, y_signature_start + 5)
    pdf.set_text_color(0, 0, 0)

    if stamp_file:
        try:
            stamp_width = 25
            stamp_x = 105 + (96 - stamp_width) / 2
            stamp_y = pdf.get_y() + 2
            pdf.image(stamp_file, x=stamp_x, y=stamp_y, w=stamp_width)
        except Exception as e:
            st.warning(f"Could not add stamp: {e}")

    pdf.set_xy(105, y_signature_start + 10 + right_signature_box_height - 10)
    pdf.set_font(pdf.default_font, "B", 10)
    pdf.cell(96, 5, "Authorized Signatory", border=0, ln=True, align="C")

    pdf.set_xy(105, y_signature_start + 6)
    pdf.cell(96, right_signature_box_height, "", border="LRB")

    pdf.set_y(max(y_after_left_signature, y_signature_start + 6 + right_signature_box_height))

    pdf_bytes = pdf.output(dest="S").encode('latin-1') if isinstance(pdf.output(dest="S"), str) else pdf.output(dest="S")
    return pdf_bytes

# --- PDF Class ---
class PO_PDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=False, margin=10)
        self.set_left_margin(15)
        self.set_right_margin(15)
        self.logo_path = None
        font_dir = os.path.join(os.path.dirname(__file__), "fonts")
        try:
            self.add_font("Calibri", "", os.path.join(font_dir, "calibri.ttf"), uni=True)
            self.add_font("Calibri", "B", os.path.join(font_dir, "calibrib.ttf"), uni=True)
            self.add_font("Calibri", "I", os.path.join(font_dir, "calibrii.ttf"), uni=True)
            self.add_font("Calibri", "BI", os.path.join(font_dir, "calibriz.ttf"), uni=True)
            self.default_font = "Calibri"
        except:
            self.default_font = "Helvetica"

        self.website_url = "https://yourcompany.com/"
    def header(self):
        self.ln(5)
        if self.page_no() == 1:
            self.ln(1)
            if self.logo_path and os.path.exists(self.logo_path):
                self.image(self.logo_path, x=155, y=8, w=50,link=self.website_url)
                self.ln(4)
            self.set_font(self.default_font, "BU", 15)
            self.cell(0, 15, "PURCHASE ORDER", ln=True, align="C")
            self.ln(1)

            self.set_font(self.default_font, "", 12)
            self.set_xy(140,33)
            self.multi_cell(60,4,
                            f"PO No: {self.sanitize_text(st.session_state.po_number)}\n"
                            f"Date: {self.sanitize_text(st.session_state.po_date)}")

    def footer(self):
        self.set_y(-12)
        
        self.set_font("Helvetica", "", 10)
        self.cell(0, 4, "[Your Company Address]", ln=True, align="C")
        
        self.set_font("Helvetica", "U", 10)
        self.set_text_color(0, 0, 255)
        
        email1 = "info@yourcompany.com"
        phone_number = "+91 00000 00000"
        website = "www.yourcompany.com"
        
        contact_text = f"{email1} | {phone_number} | {website}"
        contact_width = self.get_string_width(contact_text)
        x_contact = (self.w - contact_width) / 2
        
        self.set_x(x_contact)
        self.cell(self.get_string_width(email1), 4, email1, link=f"mailto:{email1}")
        self.set_x(x_contact + self.get_string_width(email1) + self.get_string_width(" | "))
        self.cell(self.get_string_width(phone_number), 4, phone_number, link=f"tel:{phone_number}")
        self.set_x(x_contact + self.get_string_width(email1) + self.get_string_width(" | ") + self.get_string_width(phone_number) + self.get_string_width(" | "))
        self.cell(self.get_string_width(website), 4, website, link="https://www.yourcompany.com/")
        
        self.set_text_color(0, 0, 0)

    def section_title(self, title):
        self.set_font(self.default_font, "B", 12)
        self.cell(0, 6, self.sanitize_text(title), ln=True)
        self.ln(1)

    def sanitize_text(self, text):
        return text.encode('ascii', 'ignore').decode('ascii')

def number_to_words(number):
    """Convert number to words"""
    try:
        from num2words import num2words
        return num2words(number, lang='en_IN').title() + " Rupees Only/-"
    except ImportError:
        words = f"Rupees {number:,.2f} Only/-"
        return words

def create_po_pdf(po_data, logo_path=None):
    pdf = PO_PDF()
    pdf.logo_path = logo_path
    pdf.add_page()

    sanitized_vendor_name = pdf.sanitize_text(po_data['vendor_name'])
    sanitized_vendor_address = pdf.sanitize_text(po_data['vendor_address'])
    sanitized_vendor_contact = pdf.sanitize_text(po_data['vendor_contact'])
    sanitized_vendor_mobile = pdf.sanitize_text(po_data['vendor_mobile'])
    sanitized_gst_no = pdf.sanitize_text(po_data['gst_no'])
    sanitized_pan_no = pdf.sanitize_text(po_data['pan_no'])
    sanitized_msme_no = pdf.sanitize_text(po_data['msme_no'])
    sanitized_bill_to_company = pdf.sanitize_text(po_data['bill_to_company'])
    sanitized_bill_to_address = pdf.sanitize_text(po_data['bill_to_address'])
    sanitized_ship_to_company = pdf.sanitize_text(po_data['ship_to_company'])
    sanitized_ship_to_address = pdf.sanitize_text(po_data['ship_to_address'])
    sanitized_end_company = pdf.sanitize_text(po_data['end_company'])
    sanitized_end_address = pdf.sanitize_text(po_data['end_address'])
    sanitized_end_person = pdf.sanitize_text(po_data['end_person'])
    sanitized_end_mobile = pdf.sanitize_text(po_data['end_mobile'])
    sanitized_end_email = pdf.sanitize_text(po_data['end_email'])
    sanitized_payment_terms = pdf.sanitize_text(po_data['payment_terms'])
    sanitized_delivery_terms = pdf.sanitize_text(po_data['delivery_terms'])
    sanitized_prepared_by = pdf.sanitize_text(po_data['prepared_by'])
    sanitized_authorized_by = pdf.sanitize_text(po_data['authorized_by'])
    sanitized_company_name = pdf.sanitize_text(po_data['company_name'])
    
    pdf.set_font(pdf.default_font, "B", 12)
    pdf.section_title("To:")

    pdf.set_font(pdf.default_font, "B", 12)
    pdf.multi_cell(90, 5, sanitized_vendor_name)

    pdf.set_font(pdf.default_font, "", 12)
    pdf.multi_cell(90, 5, sanitized_vendor_address)

    pdf.set_font(pdf.default_font, "B", 12)
    pdf.write(5, "Kind Attend: ")
    pdf.set_font(pdf.default_font, "", 12)
    pdf.multi_cell(95, 5, sanitized_vendor_contact)

    pdf.set_font(pdf.default_font, "B", 12)
    pdf.write(5, "Mobile: ")
    pdf.set_font(pdf.default_font, "", 12)
    pdf.multi_cell(95, 5, sanitized_vendor_mobile)

    pdf.ln(5)

    start_y = pdf.get_y()

    pdf.set_font(pdf.default_font, "B", 12)
    pdf.cell(90, 5, "Bill To:", ln=1)

    pdf.set_font(pdf.default_font, "B", 12)
    pdf.multi_cell(90, 5, sanitized_bill_to_company)

    pdf.set_font(pdf.default_font, "", 12)
    pdf.multi_cell(90, 5, sanitized_bill_to_address)

    y_after_bill = pdf.get_y()

    pdf.set_xy(110, start_y)
    pdf.set_font(pdf.default_font, "B", 12)
    pdf.cell(90, 5, "Ship To:", ln=1)
    pdf.set_x(110)

    pdf.set_font(pdf.default_font, "B", 12)
    pdf.multi_cell(90, 5, sanitized_ship_to_company)

    pdf.set_x(110)
    pdf.set_font(pdf.default_font, "", 12)
    pdf.multi_cell(90, 5, sanitized_ship_to_address)

    y_after_ship = pdf.get_y()

    pdf.set_y(max(y_after_bill, y_after_ship))
    pdf.ln(2)
    
    pdf.set_font(pdf.default_font, "B", 12)
    pdf.write(5, "GST NO: ")
    pdf.set_font(pdf.default_font, "", 12)
    pdf.multi_cell(0, 5, sanitized_gst_no)

    pdf.set_font(pdf.default_font, "B", 12)
    pdf.write(5, "PAN NO: ")
    pdf.set_font(pdf.default_font, "", 12)
    pdf.multi_cell(0, 5, sanitized_pan_no)

    pdf.set_font(pdf.default_font, "B", 12)
    pdf.write(5, "MSME Registration No: ")
    pdf.set_font(pdf.default_font, "", 12)
    pdf.multi_cell(0, 5, sanitized_msme_no)

    pdf.ln(2)

    col_widths = [65, 22, 30, 25, 15, 22]
    headers = ["Product", "Basic", "GST TAX @ 18%", "Per Unit Price", "Qty.", "Total"]
    pdf.set_fill_color(220, 220, 220)
    pdf.set_font(pdf.default_font, "B", 12)
    for h, w in zip(headers, col_widths):
        pdf.cell(w, 6, pdf.sanitize_text(h), border=1, align="C", fill=True)
    pdf.ln()

    pdf.set_font(pdf.default_font, "", 12)
    line_height = 5

    products_total = 0
    for p in po_data["products"]:
        gst_amt = p["basic"] * p["gst_percent"] / 100
        per_unit_price = p["basic"] + gst_amt
        total = per_unit_price * p["qty"]
        products_total += total

    rounded_total = round(products_total)
    round_off = rounded_total - products_total

    for p in po_data["products"]:
        gst_amt = p["basic"] * p["gst_percent"] / 100
        per_unit_price = p["basic"] + gst_amt
        total = per_unit_price * p["qty"]
        name = pdf.sanitize_text(p["name"])

        num_lines = pdf.multi_cell(col_widths[0], line_height, name, border=0, split_only=True)
        max_lines = max(len(num_lines), 1)
        row_height = line_height * max_lines

        x_start = pdf.get_x()
        y_start = pdf.get_y()

        pdf.multi_cell(col_widths[0], line_height, name, border=1)
        pdf.set_xy(x_start + col_widths[0], y_start)
        pdf.cell(col_widths[1], row_height, f"{p['basic']:,.2f}", border=1, align="R")
        pdf.cell(col_widths[2], row_height, f"{gst_amt:,.2f}", border=1, align="R")
        pdf.cell(col_widths[3], row_height, f"{per_unit_price:,.2f}", border=1, align="R")
        pdf.cell(col_widths[4], row_height, f"{p['qty']:.2f}", border=1, align="C")
        pdf.cell(col_widths[5], row_height, f"{total:,.2f}", border=1, align="R")
        pdf.ln(row_height)

    pdf.set_font(pdf.default_font, "B", 12)
    pdf.cell(sum(col_widths[:-1]), 6, "Round Off", border=1, align="R")
    pdf.cell(col_widths[5], 6, f"{round_off:,.2f}", border=1, align="R")
    pdf.ln()

    pdf.set_font(pdf.default_font, "B", 12)
    pdf.cell(sum(col_widths[:-1]), 6, "Final Amount to be Paid", border=1, align="R")
    pdf.cell(col_widths[5], 6, f"{rounded_total:,.2f}", border=1, align="R")
    pdf.ln(4)

    pdf.ln(5)
    pdf.set_font(pdf.default_font, "B", 12)
    pdf.cell(45, 4, "Amount in Words")
    pdf.cell(5, 4, ":")
    pdf.set_font(pdf.default_font, "", 12)
    pdf.multi_cell(0, 4, pdf.sanitize_text(po_data['amount_words']))

    pdf.set_font(pdf.default_font, "B", 12)

    pdf.cell(45, 5, "Taxes")
    pdf.cell(5, 4, ":")
    pdf.set_font(pdf.default_font, "", 12)
    pdf.multi_cell(0, 5, f"As specified above")

    pdf.set_font(pdf.default_font, "B", 12)
    pdf.cell(45, 5, "Payment")
    pdf.cell(5, 4, ":")
    pdf.set_font(pdf.default_font, "", 12)
    pdf.multi_cell(0, 5, f"{sanitized_payment_terms}")

    pdf.set_font(pdf.default_font, "B", 12)
    pdf.cell(45, 5, "Delivery")
    pdf.cell(5, 4, ":")
    pdf.set_font(pdf.default_font, "", 12)
    pdf.multi_cell(0, 5, f"{sanitized_delivery_terms}")

    pdf.ln(2)

    pdf.section_title("End User Details")
    pdf.set_font(pdf.default_font, "", 12)

    pdf.set_font(pdf.default_font, "B", 12)
    pdf.cell(45, 5, "Company Name")
    pdf.cell(5, 4, ":")
    pdf.set_font(pdf.default_font, "", 12)
    pdf.multi_cell(0, 5, f"{sanitized_end_company}")

    pdf.set_font(pdf.default_font, "B", 12)
    pdf.cell(45, 5, "Company Address")
    pdf.cell(5, 4, ":")
    pdf.set_font(pdf.default_font, "", 12)
    pdf.multi_cell(0, 5, f"{sanitized_end_address}")

    pdf.set_font(pdf.default_font, "B", 12)
    pdf.cell(45, 5, "Contact")
    pdf.cell(5, 4, ":")
    pdf.set_font(pdf.default_font, "", 12)
    pdf.multi_cell(0, 5, f"{sanitized_end_person}")

    pdf.set_font(pdf.default_font, "B", 12)
    pdf.cell(45, 5, "Mobile No:")
    pdf.cell(5, 4, ":")
    pdf.set_font(pdf.default_font, "", 12)
    pdf.multi_cell(0, 5, f"{sanitized_end_mobile}")

    pdf.set_font(pdf.default_font, "B", 12)
    pdf.cell(45, 5, "Email")
    pdf.cell(5, 4, ":")
    pdf.set_font(pdf.default_font, "", 12)
    pdf.multi_cell(0, 5, f"{sanitized_end_email}")

    pdf.ln(5)
    pdf.set_font(pdf.default_font, "", 12)
    pdf.cell(0, 5, f"For, {sanitized_company_name}", ln=True, border=0, align="L")
    stamp_path = None
    if stamp_path and os.path.exists(stamp_path):
        pdf.ln(2)
        pdf.image(stamp_path, x=pdf.get_x(), y=pdf.get_y(), w=25)
        pdf.ln(15)

    pdf_bytes = pdf.output(dest="S").encode('latin-1')
    return pdf_bytes

def safe_str_state(key, default=""):
    """Ensure session_state value exists and is always a string."""
    if key not in st.session_state or not isinstance(st.session_state[key], str):
        st.session_state[key] = str(default)
    return st.session_state[key] 

def safe_image_path(image_path, default_name):
    """Safely handle image paths, return None if file doesn't exist"""
    if image_path and os.path.exists(image_path):
        return image_path
    else:
        st.sidebar.warning(f"⚠ {default_name} not found")
        return None

def load_images_from_github():
    """Download images from GitHub"""
    logo_path = None
    stamp_path = None
    
    try:
        if LOGO_URL:
            logo_response = requests.get(LOGO_URL, timeout=10)
            if logo_response.status_code == 200:
                logo_path = "github_logo.jpg"
                with open(logo_path, "wb") as f:
                    f.write(logo_response.content)
    except Exception as e:
        st.sidebar.warning(f"⚠ Logo download failed: {str(e)}")
    
    try:
        if STAMP_URL:
            stamp_response = requests.get(STAMP_URL, timeout=10)
            if stamp_response.status_code == 200:
                stamp_path = "github_stamp.jpg"
                with open(stamp_path, "wb") as f:
                    f.write(stamp_response.content)
    except Exception as e:
        st.sidebar.warning(f"⚠ Stamp download failed: {str(e)}")
    
    return logo_path, stamp_path

def save_uploaded_file(uploaded_file, filename):
    """Save uploaded file to disk"""
    try:
        with open(filename, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return filename
    except Exception as e:
        st.sidebar.error(f"Error saving {filename}: {str(e)}")
        return None

# --- The main function ---
def main():
    st.set_page_config(page_title="Document Generator", page_icon="📑", layout="wide")
    st.title("📑 Document Generator - Invoice, PO & Quotation")

    # --- Logo and Stamp Configuration in Sidebar ---
    st.sidebar.header("📷 Company Branding")
    
    use_github = st.sidebar.checkbox("Use GitHub Images", value=False, 
                                   help="Use logo and stamp from GitHub repository")
    
    uploaded_logo = None
    uploaded_stamp = None
    
    if not use_github:
        st.sidebar.subheader("Upload Custom Images")
        uploaded_logo = st.sidebar.file_uploader("Upload Company Logo", 
                                               type=["png", "jpg", "jpeg"], 
                                               key="global_logo")
        uploaded_stamp = st.sidebar.file_uploader("Upload Company Stamp", 
                                                type=["png", "jpg", "jpeg"], 
                                                key="global_stamp")
    
    global_logo_path = None
    global_stamp_path = None
    
    if use_github:
        with st.sidebar.status("Loading images from GitHub..."):
            global_logo_path, global_stamp_path = load_images_from_github()
            
            if global_logo_path:
                st.sidebar.success("✓ GitHub logo loaded")
            else:
                st.sidebar.error("❌ GitHub logo failed")
                
            if global_stamp_path:
                st.sidebar.success("✓ GitHub stamp loaded")
            else:
                st.sidebar.error("❌ GitHub stamp failed")
    else:
        if uploaded_logo:
            global_logo_path = save_uploaded_file(uploaded_logo, "custom_logo.jpg")
            if global_logo_path:
                st.sidebar.success("✓ Custom logo loaded")
        
        if uploaded_stamp:
            global_stamp_path = save_uploaded_file(uploaded_stamp, "custom_stamp.jpg")
            if global_stamp_path:
                st.sidebar.success("✓ Custom stamp loaded")
    
    st.sidebar.subheader("Image Status")
    if global_logo_path:
        st.sidebar.info("Logo: ✅ Loaded")
    else:
        st.sidebar.error("Logo: ❌ Not available")
    
    if global_stamp_path:
        st.sidebar.info("Stamp: ✅ Loaded")
    else:
        st.sidebar.error("Stamp: ❌ Not available")

    # --- Initialize Session State ---
    # Quotation session states
    if "quotation_seq" not in st.session_state:
        st.session_state.quotation_seq = get_current_quotation_sequence()
    if "quotation_products" not in st.session_state:
        st.session_state.quotation_products = []
    if "last_quotation_number" not in st.session_state:
        st.session_state.last_quotation_number = ""
    if "quotation_number" not in st.session_state:
        st.session_state.quotation_number = generate_quotation_number("SP1", st.session_state.quotation_seq)
    if "current_quote_sales_person" not in st.session_state:
        st.session_state.current_quote_sales_person = "SP1"

    # PO session states  
    if "po_seq" not in st.session_state:
        st.session_state.po_seq = get_current_po_sequence()
    if "products" not in st.session_state:
        st.session_state.products = []
    if "company_name" not in st.session_state:
        st.session_state.company_name = "Your Company Name"
    if "po_number" not in st.session_state:
        st.session_state.po_number = generate_po_number("SP1", st.session_state.po_seq)
    if "po_date" not in st.session_state:
        st.session_state.po_date = datetime.date.today().strftime("%d-%m-%Y")
    if "last_po_number" not in st.session_state:
        st.session_state.last_po_number = ""
    if "current_po_sales_person" not in st.session_state:
        st.session_state.current_po_sales_person = "SP1"
    if "current_po_quarter" not in st.session_state:
        st.session_state.current_po_quarter = get_current_quarter()

    # Invoice session states
    if "invoice_seq" not in st.session_state:
        st.session_state.invoice_seq = get_current_invoice_sequence()
    if "invoice_number" not in st.session_state:
        st.session_state.invoice_number = generate_invoice_number(st.session_state.invoice_seq)
    if "last_invoice_number" not in st.session_state:
        st.session_state.last_invoice_number = ""
    if "current_invoice_quarter" not in st.session_state:
        st.session_state.current_invoice_quarter = get_current_quarter()

    # Invoice buyer session states
    if "invoice_buyer_company" not in st.session_state:
        st.session_state.invoice_buyer_company = "Customer Company Ltd."
    if "invoice_buyer_address" not in st.session_state:
        st.session_state.invoice_buyer_address = "Customer Address"
    if "invoice_buyer_gst" not in st.session_state:
        st.session_state.invoice_buyer_gst = "GSTNUMBER"
    if "invoice_buyer_mobile" not in st.session_state:
        st.session_state.invoice_buyer_mobile = "00000 00000"
    if "invoice_buyer_email" not in st.session_state:
        st.session_state.invoice_buyer_email = "customer@company.com"

    # Vendor session states
    if "po_vendor_name" not in st.session_state:
        st.session_state.po_vendor_name = "Supplier Company Ltd."
    if "po_vendor_address" not in st.session_state:
        st.session_state.po_vendor_address = "Supplier Address"
    if "po_vendor_contact" not in st.session_state:
        st.session_state.po_vendor_contact = "Contact Person"
    if "po_vendor_mobile" not in st.session_state:
        st.session_state.po_vendor_mobile = "+91 00000 00000"
    if "po_gst_no" not in st.session_state:
        st.session_state.po_gst_no = "GSTNUMBER"
    if "po_pan_no" not in st.session_state:
        st.session_state.po_pan_no = "PANNUMBER"
    if "po_msme_no" not in st.session_state:
        st.session_state.po_msme_no = "MSMENUMBER"

    # Quotation end user session states
    if "quote_end_company" not in st.session_state:
        st.session_state.quote_end_company = "Customer Company Ltd."
    if "quote_end_address" not in st.session_state:
        st.session_state.quote_end_address = "Customer Address"
    if "quote_end_person" not in st.session_state:
        st.session_state.quote_end_person = "Contact Person"
    if "quote_end_mobile" not in st.session_state:
        st.session_state.quote_end_mobile = "0000000000"
    if "quote_end_email" not in st.session_state:
        st.session_state.quote_end_email = "customer@company.com"
    if "quote_end_gst_no" not in st.session_state:
        st.session_state.quote_end_gst_no = "GSTNUMBER"

    # PO end user session states
    if "po_end_company" not in st.session_state:
        st.session_state.po_end_company = "Customer Company Ltd."
    if "po_end_address" not in st.session_state:
        st.session_state.po_end_address = "Customer Address"
    if "po_end_person" not in st.session_state:
        st.session_state.po_end_person = "Contact Person"
    if "po_end_mobile" not in st.session_state:
        st.session_state.po_end_mobile = "0000000000"
    if "po_end_email" not in st.session_state:
        st.session_state.po_end_email = "customer@company.com"
    if "po_end_gst_no" not in st.session_state:
        st.session_state.po_end_gst_no = "GSTNUMBER"

    # PO bill to/ship to session states
    if "po_bill_to_company" not in st.session_state:
        st.session_state.po_bill_to_company = "Your Company Name"
    if "po_bill_to_address" not in st.session_state:
        st.session_state.po_bill_to_address = "Your Company Address"
    if "po_ship_to_company" not in st.session_state:
        st.session_state.po_ship_to_company = "Your Company Name"
    if "po_ship_to_address" not in st.session_state:
        st.session_state.po_ship_to_address = "Your Company Address"

    # --- Upload Excel and Load Vendor/End User ---
    uploaded_excel = st.file_uploader("📂 Upload Vendor & End User Excel", type=["xlsx"])

    if uploaded_excel:
        vendors_df = pd.read_excel(uploaded_excel, sheet_name="Vendors", dtype={"Mobile": str})
        endusers_df = pd.read_excel(uploaded_excel, sheet_name="EndUsers")

        st.success("✅ Excel loaded successfully!")

        vendor_name = st.selectbox("Select Vendor", vendors_df["Vendor Name"].unique())
        vendor = vendors_df[vendors_df["Vendor Name"] == vendor_name].iloc[0]

        end_user_name = st.selectbox("Select End User", endusers_df["End User Company"].unique())
        end_user = endusers_df[endusers_df["End User Company"] == end_user_name].iloc[0]

        def safe_strip(value):
            try:
                if pd.isna(value):
                    return ""
                return str(value).split(".")[0].strip()
            except Exception:
                return ""

        vendor_mobile = safe_strip(vendor.get("Mobile", ""))
        End_user_mobile = safe_strip(end_user.get("End Mobile", ""))

        st.session_state.po_vendor_name = vendor["Vendor Name"]
        st.session_state.po_vendor_address = vendor["Vendor Address"]
        st.session_state.po_vendor_contact = vendor["Contact Person"]
        st.session_state.po_vendor_mobile = vendor_mobile
        st.session_state.po_end_company = end_user["End User Company"]
        st.session_state.po_end_address = end_user["End User Address"]
        st.session_state.po_end_person = end_user["End User Contact"]
        st.session_state.po_end_mobile = End_user_mobile
        st.session_state.po_end_email = end_user["End User Email"]
        st.session_state.po_end_gst_no = end_user["GST NO"]

        st.info("Vendor & End User details auto-filled from Excel ✅")

    # Create tabs for different document types
    tab1, tab2, tab3 = st.tabs(["Quotation Generator", "Purchase Order Generator", "Tax Invoice Generator"])

    with tab1:
        if global_logo_path and os.path.exists(global_logo_path):
            st.image(global_logo_path, width=150)
            st.markdown("### Quotation Generator")
        else:
            st.header("Quotation Generator")  
        
        today = datetime.date.today()
        current_quarter = get_current_quarter()
        
        st.sidebar.header("Quotation Settings")
        sales_person = st.sidebar.selectbox("Select Sales Person", 
                                        options=list(SALES_PERSON_MAPPING.keys()), 
                                        format_func=lambda x: f"{x} - {SALES_PERSON_MAPPING[x]['name']}",
                                        key="quote_sales_person")
        
        current_sales_person_info = SALES_PERSON_MAPPING.get(sales_person, SALES_PERSON_MAPPING['SP1'])
        
        def get_quotation_number():
            if st.session_state.last_quotation_number:
                try:
                    last_prefix, last_sales_person, last_quarter, last_date, last_year_range, last_sequence = parse_quotation_number(st.session_state.last_quotation_number)
                    
                    if last_sales_person == sales_person and last_quarter == current_quarter:
                        next_sequence = get_next_sequence_number(st.session_state.last_quotation_number)
                        return generate_quotation_number(sales_person, next_sequence)
                    else:
                        return generate_quotation_number(sales_person, 1)
                except:
                    return generate_quotation_number(sales_person, st.session_state.quotation_seq)
            else:
                return generate_quotation_number(sales_person, st.session_state.quotation_seq)
        
        if "current_quote_sales_person" not in st.session_state:
            st.session_state.current_quote_sales_person = sales_person
            st.session_state.quotation_number = get_quotation_number()
        
        if (st.session_state.current_quote_sales_person != sales_person or 
            st.session_state.get('current_quarter', '') != current_quarter):
            st.session_state.current_quote_sales_person = sales_person
            st.session_state.current_quarter = current_quarter
            st.session_state.quotation_number = get_quotation_number()
        
        st.sidebar.info(f"**Current Sales Person:** {current_sales_person_info['name']}")
        st.sidebar.info(f"**Current Quarter:** {current_quarter}")
        
        try:
            prefix, current_sp, quarter, date_part, year_range, sequence = parse_quotation_number(st.session_state.quotation_number)
            st.sidebar.success(f"**Auto-generated Quotation Number**")
            st.sidebar.info(f"**Format:** {current_sp}/{quarter}/{date_part}/{year_range}_{sequence}")
        except:
            st.sidebar.warning("Could not parse quotation number")
        
        st.sidebar.subheader("Quotation Number Editor")
        
        try:
            current_prefix, current_sp, current_q, current_date, current_year_range, current_seq = parse_quotation_number(st.session_state.quotation_number)
            
            col1, col2, col3, col4 = st.sidebar.columns([1, 2, 2, 1])
            
            with col1:
                st.text_input("Sales Person", value=current_sp, key="quote_sp_display", disabled=True)
            
            with col2:
                new_date = st.text_input("Date", value=current_date, key="quote_date_edit")
            
            with col3:
                new_year_range = st.text_input("Year Range", value=current_year_range, key="quote_year_edit")
            
            with col4:
                new_sequence = st.number_input("Sequence", 
                                            min_value=1, 
                                            value=int(current_seq), 
                                            step=1,
                                            key="quote_seq_edit")
            
            new_quotation_number = f"COM/{sales_person}/{current_q}/{new_date}/{new_year_range}_{new_sequence:03d}"
            
            if new_quotation_number != st.session_state.quotation_number:
                st.session_state.quotation_number = new_quotation_number
                
        except Exception as e:
            st.sidebar.error(f"Error parsing quotation number: {e}")
            st.session_state.quotation_number = generate_quotation_number(sales_person, st.session_state.quotation_seq)
        
        st.sidebar.code(st.session_state.quotation_number)
        
        quotation_auto_increment = st.sidebar.checkbox("Auto-increment Sequence", value=True, key="quote_auto_increment")
        
        if st.sidebar.button("Reset to Auto-generate", use_container_width=True):
            st.session_state.quotation_seq = 1
            st.session_state.last_quotation_number = ""
            st.session_state.quotation_number = get_quotation_number()
            st.sidebar.success("Quotation number reset to auto-generated")
            st.rerun()
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.header("Recipient Details")
            
            selected_enduser_quote = st.selectbox(
                "Select Company", 
                options=get_enduser_dropdown_options(),
                key="enduser_dropdown_quote"
            )
            
            if selected_enduser_quote and selected_enduser_quote != "Select End User":
                enduser_data = END_USER_DATABASE.get(selected_enduser_quote, {})
                st.session_state.quote_end_company = selected_enduser_quote
                st.session_state.quote_end_address = enduser_data.get("address", "")
                st.session_state.quote_end_person = enduser_data.get("contact", "")
                st.session_state.quote_end_mobile = enduser_data.get("mobile", "")
                st.session_state.quote_end_email = enduser_data.get("email", "")
                st.session_state.quote_end_gst_no = enduser_data.get("gst_no", "")
            
            vendor_name = st.text_input("Company Name", 
                                    value=st.session_state.get("quote_end_company", "Customer Company Ltd."), 
                                    key="quote_end_company")
            vendor_address = st.text_area("Company Address", 
                                        value=st.session_state.get("quote_end_address", "Customer Address"), 
                                        key="quote_end_address")
            vendor_email = st.text_input("Email", 
                                    value=st.session_state.get("quote_end_email", "customer@company.com"), 
                                    key="quote_end_email")
            vendor_contact = st.text_input("Contact Person (Kind Attention)", 
                                        value=st.session_state.get("quote_end_person", "Contact Person"), 
                                        key="quote_end_person")
            vendor_mobile = st.text_input("Mobile", 
                                        value=st.session_state.get("quote_end_mobile", "0000000000"), 
                                        key="quote_end_mobile")
            
            vendor_gst = st.text_input("GST No (Optional)", 
                                    value=st.session_state.get("quote_end_gst_no", ""), 
                                    key="quote_end_gst_no")

            st.header("Quotation Details")
            price_validity = st.text_input("Price Validity", "10 days from Quotation date", key="quote_price_validity")
            subject_line = st.text_input("Subject", "Proposal for Software Services", key="quote_subject")
            intro_paragraphs_1 = st.text_area("Introduction Paragraph",
            "This is with reference to your requirement for software services.",
            key="quote_intro"
            )

        
        with col2:
            st.header("Products & Services")
            
            col_annexure, col_title = st.columns(2)
            
            with col_annexure:
                annexure_text = st.text_input(
                    "Annexure Text", 
                    "Annexure I - Commercials", 
                    key="quote_annexure_input",
                    help="Enter annexure text"
                )
            
            with col_title:
                quotation_title = st.text_input(
                    "Quotation Title", 
                    "Quotation for Software Services", 
                    key="quote_title_input",
                    help="Enter the main title"
                )
            
            st.subheader("Add Products")
            selected_product = st.selectbox("Select from Catalog", [""] + list(PRODUCT_CATALOG.keys()), key="quote_product_select_catalog")
            
            if st.button("➕ Add Selected Product", key="quote_add_selected_product"):
                if selected_product:
                    details = PRODUCT_CATALOG[selected_product]
                    st.session_state.quotation_products.append({
                        "name": selected_product,
                        "basic": details["basic"],
                        "gst_percent": details["gst_percent"],
                        "qty": 1.0,
                    })
                    st.success(f"{selected_product} added!")
            
            if st.button("➕ Add Empty Product", key="quote_add_empty_product"):
                st.session_state.quotation_products.append({"name": "New Product", "basic": 0.0, "gst_percent": 18.0, "qty": 1.0})

            st.subheader("Current Products")
            for i, p in enumerate(st.session_state.quotation_products):
                with st.expander(f"Product {i+1}: {p['name']}", expanded=i == 0):
                    st.session_state.quotation_products[i]["name"] = st.text_input("Name", p["name"], key=f"quote_name_{i}")
                    st.session_state.quotation_products[i]["basic"] = st.number_input("Basic (₹)", p["basic"], format="%.2f", key=f"quote_basic_{i}")
                    st.session_state.quotation_products[i]["gst_percent"] = st.number_input("GST %", p["gst_percent"], format="%.1f", key=f"quote_gst_{i}")
                    st.session_state.quotation_products[i]["qty"] = st.number_input("Qty", p["qty"], format="%.2f", key=f"quote_qty_{i}")
                    if st.button("Remove", key=f"quote_remove_{i}"):
                        st.session_state.quotation_products.pop(i)
                        st.rerun()
        
        st.header("Preview & Generate Quotation")
        
        st.info(f"**Quotation Number:** {st.session_state.quotation_number}")
        st.info(f"**Sales Person:** {current_sales_person_info['name']} ({sales_person}) - {current_sales_person_info['email']}")
        
        totals = calculate_quotation_totals(st.session_state.quotation_products)
        
        total_base = sum(p["basic"] * p["qty"] for p in st.session_state.quotation_products)
        total_gst = sum(p["basic"] * p["gst_percent"] / 100 * p["qty"] for p in st.session_state.quotation_products)
        grand_total = total_base + total_gst
        amount_words = num2words(grand_total, to="currency", currency="INR").title()
        
        col3, col4, col5 = st.columns(3)
        with col3:
            st.metric("Total Base Amount", f"₹{total_base:,.2f}")
        with col4:
            st.metric("Total GST", f"₹{total_gst:,.2f}")
        with col5:
            st.metric("Grand Total", f"₹{grand_total:,.2f}")
        
        st.subheader("Company Branding")
        st.info("Using global logo and stamp from sidebar settings")
        logo_path = global_logo_path
        stamp_path = global_stamp_path

        if not logo_path:
            st.warning("⚠ No company logo available")
        if not stamp_path:
            st.warning("⚠ No company stamp available")
        
        if st.button("Generate Quotation PDF", type="primary", use_container_width=True, key="generate_quote"):
            if not st.session_state.quotation_products:
                st.error("Please add at least one product to generate the quotation.")
            else:
                products_total = 0
                for p in st.session_state.quotation_products:
                    gst_amt = p["basic"] * p["gst_percent"] / 100
                    per_unit_price = p["basic"] + gst_amt
                    total = per_unit_price * p["qty"]
                    products_total += total

                rounded_total = round(products_total)
                round_off = rounded_total - products_total

                grand_total = rounded_total
                amount_words = number_to_words(rounded_total)

                quotation_data = {
                    "quotation_number": st.session_state.quotation_number,
                    "quotation_date": today.strftime("%d-%m-%Y"),
                    "vendor_name": vendor_name,
                    "vendor_address": vendor_address,
                    "vendor_email": vendor_email,
                    "vendor_contact": vendor_contact,
                    "vendor_mobile": vendor_mobile,
                    "products": st.session_state.quotation_products,
                    "price_validity": price_validity,
                    "grand_total": grand_total,
                    "round_off": round_off,
                    "amount_words": amount_words,
                    "subject": subject_line,
                    "intro_paragraph": intro_paragraphs_1,
                    "product_name": selected_product if selected_product else "Software",   
                    "sales_person_code": sales_person,  
                    "annexure_text": annexure_text,  
                    "quotation_title": quotation_title
                }
                
                try:
                    pdf_bytes = create_quotation_pdf(quotation_data, logo_path, stamp_path)
                    
                    st.session_state.last_quotation_number = st.session_state.quotation_number
                    
                    if quotation_auto_increment:
                        next_sequence = get_next_quotation_sequence()
                        st.session_state.quotation_seq = next_sequence
                    
                    st.success("✅ Quotation generated successfully!")
                    st.info(f"📧 Sales Person: {current_sales_person_info['name']}")
                    
                    st.download_button(
                        "⬇ Download Quotation PDF",
                        data=pdf_bytes,
                        file_name=f"{vendor_name}_{st.session_state.quotation_number.replace('/', '_')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                    
                except Exception as e:
                    st.error(f"Error generating PDF: {str(e)}")

    with tab2:
        if global_logo_path and os.path.exists(global_logo_path):
            st.image(global_logo_path, width=150)
            st.markdown("### Purchase Order Generator")
        else:
            st.header("Purchase Order Generator")  
        
        today = datetime.date.today()
        current_quarter = get_current_quarter()
        
        st.sidebar.header("PO Settings")
        
        po_sales_person = st.sidebar.selectbox("Select Sales Person", 
                                            options=list(SALES_PERSON_MAPPING.keys()), 
                                            format_func=lambda x: f"{x} - {SALES_PERSON_MAPPING[x]['name']}",
                                            key="po_sales_person_select")
        
        current_sales_person_info = SALES_PERSON_MAPPING.get(po_sales_person, SALES_PERSON_MAPPING['SP1'])
        
        def get_po_number():
            if st.session_state.last_po_number:
                try:
                    last_prefix, last_sales_person, last_year, last_quarter, last_sequence = parse_po_number(st.session_state.last_po_number)
                    
                    if last_sales_person == po_sales_person and last_quarter == current_quarter:
                        next_sequence = get_next_sequence_number_po(st.session_state.last_po_number)
                        return generate_po_number(po_sales_person, next_sequence)
                    else:
                        return generate_po_number(po_sales_person, 1)
                except:
                    return generate_po_number(po_sales_person, st.session_state.po_seq)
            else:
                return generate_po_number(po_sales_person, st.session_state.po_seq)
        
        if "current_po_sales_person" not in st.session_state:
            st.session_state.current_po_sales_person = po_sales_person
            st.session_state.po_number = get_po_number()
        
        if (st.session_state.current_po_sales_person != po_sales_person or 
            st.session_state.get('current_po_quarter', '') != current_quarter):
            st.session_state.current_po_sales_person = po_sales_person
            st.session_state.current_po_quarter = current_quarter
            st.session_state.po_number = get_po_number()
        
        st.sidebar.info(f"**Current Sales Person:** {current_sales_person_info['name']}")
        st.sidebar.info(f"**Current Quarter:** {current_quarter}")
        
        try:
            prefix, current_sp, year, quarter, sequence = parse_po_number(st.session_state.po_number)
            st.sidebar.success(f"**Auto-generated PO Number**")
            st.sidebar.info(f"**Format:** {current_sp}/{year}/{quarter}_{sequence}")
        except:
            st.sidebar.warning("Could not parse PO number")
        
        st.sidebar.subheader("PO Number Editor")
        
        try:
            current_prefix, current_sp, current_year, current_q, current_seq = parse_po_number(st.session_state.po_number)
            
            col1, col2, col3, col4 = st.sidebar.columns([1, 2, 2, 1])
            
            with col1:
                st.text_input("Sales Person", value=current_sp, key="po_sp_display", disabled=True)
            
            with col2:
                new_year = st.text_input("Year", value=current_year, key="po_year_edit")
            
            with col3:
                new_quarter = st.text_input("Quarter", value=current_q, key="po_quarter_edit")
            
            with col4:
                new_sequence = st.number_input("Sequence", 
                                            min_value=1, 
                                            value=int(current_seq), 
                                            step=1,
                                            key="po_seq_edit")
            
            new_po_number = f"COM/{po_sales_person}/{new_year}/{new_quarter}_{new_sequence:03d}"
            
            if new_po_number != st.session_state.po_number:
                st.session_state.po_number = new_po_number
                
        except Exception as e:
            st.sidebar.error(f"Error parsing PO number: {e}")
            st.session_state.po_number = generate_po_number(po_sales_person, st.session_state.po_seq)
        
        st.sidebar.code(st.session_state.po_number)
        
        po_auto_increment = st.sidebar.checkbox("Auto-increment Sequence", value=True, key="po_auto_increment_checkbox")
        
        if st.sidebar.button("Reset to Auto-generate", use_container_width=True, key="po_reset_auto_generate"):
            st.session_state.po_seq = 1
            st.session_state.last_po_number = ""
            st.session_state.po_number = get_po_number()
            st.sidebar.success("PO number reset to auto-generated")
            st.rerun()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Vendor & End User Details")
            
            selected_vendor = st.selectbox(
                "Select Vendor", 
                options=get_vendor_dropdown_options(),
                key="vendor_dropdown_po"
            )
            
            if selected_vendor and selected_vendor != "Select Vendor":
                update_vendor_fields(selected_vendor)
            
            st.subheader("Vendor Details")
            vendor_name = st.text_input(
                "Vendor Name",
                value=st.session_state.get("po_vendor_name", "Supplier Company Ltd."),
                key="po_vendor_name"
            )
            vendor_address = st.text_area(
                "Vendor Address",
                value=st.session_state.get("po_vendor_address", "Supplier Address"),
                key="po_vendor_address"
            )
            vendor_contact = st.text_input(
                "Contact Person",
                value=st.session_state.get("po_vendor_contact", "Contact Person"),
                key="po_vendor_contact"
            )
            vendor_mobile = st.text_input(
                "Mobile",
                value=st.session_state.get("po_vendor_mobile", "+91 00000 00000"),
                key="po_vendor_mobile"
            )
            
            st.subheader("End User Details")
            
            selected_enduser = st.selectbox(
                "Select End User", 
                options=get_enduser_dropdown_options(),
                key="enduser_dropdown_po"
            )
            
            if selected_enduser and selected_enduser != "Select End User":
                update_enduser_fields(selected_enduser)
            
            end_company = st.text_input(
                "End User Company",
                value=st.session_state.get("po_end_company", "Customer Company Ltd."),
                key="po_end_company"
            )
            end_address = st.text_area(
                "End User Address",
                value=st.session_state.get("po_end_address", "Customer Address"),
                key="po_end_address"
            )
            end_person = st.text_input(
                "End User Contact",
                value=st.session_state.get("po_end_person", "Contact Person"),
                key="po_end_person"
            )
            end_mobile = st.text_input(
                "End Mobile",
                value=str(st.session_state.get("po_end_mobile", "0000000000") or "").strip(),
                key="po_end_mobile"
            )
            end_email = st.text_input(
                "End User Email",
                value=st.session_state.get("po_end_email", "customer@company.com"),
                key="po_end_email"
            )
            
            st.subheader("Products")
            selected_product = st.selectbox("Select from Catalog", [""] + list(PRODUCT_CATALOG.keys()), key="po_product_select_catalog")
            
            col_add1, col_add2 = st.columns(2)
            with col_add1:
                if st.button("➕ Add Selected Product", key="po_add_selected_product", use_container_width=True):
                    if selected_product:
                        details = PRODUCT_CATALOG[selected_product]
                        st.session_state.products.append({
                            "name": selected_product,
                            "basic": details["basic"],
                            "gst_percent": details["gst_percent"],
                            "qty": 1.0,
                        })
                        st.success(f"{selected_product} added!")
                        st.rerun()
            with col_add2:
                if st.button("➕ Add Empty Product", key="po_add_empty_product", use_container_width=True):
                    st.session_state.products.append({"name": "New Product", "basic": 0.0, "gst_percent": 18.0, "qty": 1.0})
                    st.rerun()

            for i, p in enumerate(st.session_state.products):
                with st.expander(f"Product {i+1}: {p['name']}", expanded=True):
                    col_prod1, col_prod2, col_prod3, col_prod4 = st.columns([3, 2, 2, 1])
                    with col_prod1:
                        st.session_state.products[i]["name"] = st.text_input("Name", p["name"], key=f"po_name_{i}")
                    with col_prod2:
                        st.session_state.products[i]["basic"] = st.number_input("Basic (₹)", p["basic"], format="%.2f", key=f"po_basic_{i}")
                    with col_prod3:
                        st.session_state.products[i]["gst_percent"] = st.number_input("GST %", p["gst_percent"], format="%.1f", key=f"po_gst_{i}")
                    with col_prod4:
                        st.session_state.products[i]["qty"] = st.number_input("Qty", p["qty"], format="%.2f", key=f"po_qty_{i}")
                    if st.button("Remove", key=f"po_remove_{i}", use_container_width=True):
                        st.session_state.products.pop(i)
                        st.rerun()

        with col2:
            st.subheader("Company & Tax Details")
            
            bill_to_company = st.text_input(
                "Bill To",
                value=safe_str_state("po_bill_to_company", "Your Company Name"),
                key="po_bill_to_company_input"
            )
            bill_to_address = st.text_area(
                "Bill To Address",
                value=safe_str_state("po_bill_to_address", "Your Company Address"),
                key="po_bill_to_address_input"
            )
            ship_to_company = st.text_input(
                "Ship To",
                value=safe_str_state("po_ship_to_company", "Your Company Name"),
                key="po_ship_to_company_input"
            )
            ship_to_address = st.text_area(
                "Ship To Address",
                value=safe_str_state("po_ship_to_address", "Your Company Address"),
                key="po_ship_to_address_input"
            )
            gst_no = st.text_input(
                "GST No",
                value=st.session_state.get("po_gst_no", "GSTNUMBER"),
                key="po_gst_no_input"
            )
            pan_no = st.text_input(
                "PAN No",
                value=st.session_state.get("po_pan_no", "PANNUMBER"),
                key="po_pan_no_input"
            )
            msme_no = st.text_input(
                "MSME No",
                value=st.session_state.get("po_msme_no", "MSMENUMBER"),
                key="po_msme_no_input"
            )
            
            st.subheader("Terms & Authorization")
            payment_terms = st.text_input("Payment Terms", "30 Days from Invoice date.", key="po_payment_terms_input")
            delivery_days = st.number_input("Delivery (Days)", min_value=1, value=2, key="po_delivery_days_input")
            delivery_terms = st.text_input("Delivery Terms", f"Within {delivery_days} Days.", key="po_delivery_terms_input")
            prepared_by = st.text_input("Prepared By", "Finance Department", key="po_prepared_by_input")
            authorized_by = st.text_input("Authorized By", "Your Company Name", key="po_authorized_by_input")
            
            st.subheader("Preview & Generate")
            
            st.info(f"**PO Number:** {st.session_state.po_number}")
            st.info(f"**Sales Person:** {current_sales_person_info['name']} ({po_sales_person}) - {current_sales_person_info['email']}")
            
            total_base = sum(p["basic"] * p["qty"] for p in st.session_state.products)
            total_gst = sum(p["basic"] * p["gst_percent"] / 100 * p["qty"] for p in st.session_state.products)
            grand_total = total_base + total_gst
            amount_words = num2words(grand_total, to="currency", currency="INR").title()
            st.metric("Grand Total", f"₹{grand_total:,.2f}")

            logo_path = global_logo_path
            if not logo_path:
                st.warning("No company logo available. Please upload one in the sidebar.")
            
            if st.button("Generate PO", type="primary", key="po_generate_button", use_container_width=True):
                products_total = 0
                for p in st.session_state.products:
                    gst_amt = p["basic"] * p["gst_percent"] / 100
                    per_unit_price = p["basic"] + gst_amt
                    total = per_unit_price * p["qty"]
                    products_total += total

                rounded_total = round(products_total)
                round_off = rounded_total - products_total

                grand_total = rounded_total
                amount_words = number_to_words(rounded_total)

                po_data = {
                    "po_number": st.session_state.po_number,
                    "po_date": st.session_state.po_date,
                    "vendor_name": vendor_name,
                    "vendor_address": vendor_address,
                    "vendor_contact": vendor_contact,
                    "vendor_mobile": vendor_mobile,
                    "gst_no": gst_no,
                    "pan_no": pan_no,
                    "msme_no": msme_no,
                    "bill_to_company": bill_to_company,
                    "bill_to_address": bill_to_address,
                    "ship_to_company": ship_to_company,
                    "ship_to_address": ship_to_address,
                    "end_company": end_company,
                    "end_address": end_address,
                    "end_person": end_person,
                    "end_mobile": end_mobile,
                    "end_email": end_email,
                    "products": st.session_state.products,
                    "grand_total": grand_total,
                    "amount_words": amount_words,
                    "payment_terms": payment_terms,
                    "delivery_terms": delivery_terms,
                    "prepared_by": prepared_by,
                    "authorized_by": authorized_by,
                    "company_name": st.session_state.company_name
                }

                pdf_bytes = create_po_pdf(po_data, logo_path)
                st.session_state.last_po_number = st.session_state.po_number
                
                if po_auto_increment:
                    next_sequence = get_next_po_sequence()
                    st.session_state.po_seq = next_sequence

                st.success("Purchase Order generated!")
                st.info(f"📧 Sales Person: {current_sales_person_info['name']}")
                
                st.download_button(
                    "⬇ Download Purchase Order",
                    data=pdf_bytes,
                    file_name=f"{end_company}_{st.session_state.po_number.replace('/', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

    with tab3:
        if global_logo_path and os.path.exists(global_logo_path):
            st.image(global_logo_path, width=150)
            st.markdown("### Tax Invoice Generator")
        else:
            st.header("Tax Invoice Generator")  
        
        today = datetime.date.today()
        current_quarter = get_current_quarter()
        
        st.sidebar.header("Invoice Settings")
        
        def get_invoice_number():
            if st.session_state.last_invoice_number:
                try:
                    last_prefix, last_year_range, last_quarter, last_sequence = parse_invoice_number(st.session_state.last_invoice_number)
                    
                    if last_quarter == current_quarter:
                        next_sequence = get_next_sequence_number_invoice(st.session_state.last_invoice_number)
                        return generate_invoice_number(next_sequence)
                    else:
                        return generate_invoice_number(1)
                except:
                    return generate_invoice_number(st.session_state.invoice_seq)
            else:
                return generate_invoice_number(st.session_state.invoice_seq)
        
        if "current_invoice_quarter" not in st.session_state:
            st.session_state.current_invoice_quarter = current_quarter
            st.session_state.invoice_number = get_invoice_number()
        
        if st.session_state.get('current_invoice_quarter', '') != current_quarter:
            st.session_state.current_invoice_quarter = current_quarter
            st.session_state.invoice_number = get_invoice_number()
        
        st.sidebar.info(f"**Current Quarter:** {current_quarter}")
        
        try:
            prefix, year_range, quarter, sequence = parse_invoice_number(st.session_state.invoice_number)
            st.sidebar.success(f"**Auto-generated Invoice Number**")
            st.sidebar.info(f"**Format:** {year_range}/{quarter}/{sequence}")
        except:
            st.sidebar.warning("Could not parse invoice number")
        
        st.sidebar.subheader("Invoice Number Editor")
        
        try:
            current_prefix, current_year_range, current_q, current_seq = parse_invoice_number(st.session_state.invoice_number)
            
            col1, col2, col3 = st.sidebar.columns([2, 2, 1])
            
            with col1:
                new_year_range = st.text_input("Year Range", value=current_year_range, key="invoice_year_edit")
            
            with col2:
                new_quarter = st.text_input("Quarter", value=current_q, key="invoice_quarter_edit")
            
            with col3:
                new_sequence = st.number_input("Sequence", 
                                            min_value=1, 
                                            value=int(current_seq), 
                                            step=1,
                                            key="invoice_seq_edit")
            
            new_invoice_number = f"COM/{new_year_range}/{new_quarter}/{new_sequence:02d}"
            
            if new_invoice_number != st.session_state.invoice_number:
                st.session_state.invoice_number = new_invoice_number
                
        except Exception as e:
            st.sidebar.error(f"Error parsing invoice number: {e}")
            st.session_state.invoice_number = generate_invoice_number(st.session_state.invoice_seq)
        
        st.sidebar.code(st.session_state.invoice_number)
        
        invoice_auto_increment = st.sidebar.checkbox("Auto-increment Sequence", value=True, key="invoice_auto_increment")
        
        if st.sidebar.button("Reset to Auto-generate", use_container_width=True, key="invoice_reset_auto_generate"):
            next_sequence = get_next_invoice_sequence()
            st.session_state.invoice_seq = next_sequence
            st.session_state.last_invoice_number = ""
            st.session_state.invoice_number = generate_invoice_number(next_sequence)
            st.sidebar.success(f"Invoice number reset to next sequence: {next_sequence}")
            st.rerun()

        col1, col2 = st.columns([1,1])
        with col1:
            st.subheader("Invoice Details")
            
            st.info(f"**Invoice Number:** {st.session_state.invoice_number}")
            
            invoice_no = st.text_input("Invoice No", st.session_state.invoice_number, key="invoice_number_input")
            invoice_date = st.text_input("Invoice Date", datetime.date.today().strftime("%d-%m-%Y"))
            Suppliers_Reference = st.text_input("Supplier's Reference", "NA")
            Others_Reference = st.text_input("Other's Reference", "NA")
            buyers_order_no = st.text_input("Buyer's Order No.", "Online")
            buyers_order_date = st.text_input("Buyer's Order Date", datetime.date.today().strftime("%d-%m-%Y"))
            dispatched_through = st.text_input("Dispatched Through", "Online")
            
            payment_terms = st.text_input("Mode/Terms of Payment", "100% Advance with Purchase")
            
            terms_of_delivery = st.text_input("Terms of delivery", "Within Month")
            
            destination = st.text_input("Destination", "City Name")
            
            st.subheader("Seller Details")
            vendor_name = st.text_input("Seller Name", "Your Company Name")
            vendor_address = st.text_area("Seller Address", "Your Company Address")
            vendor_gst = st.text_input("Seller GST No.", "GSTNUMBER")
            vendor_msme = st.text_input("Seller MSME Registration No.", "MSMENUMBER")

        with col2:
            st.subheader("Buyer Details")
            
            selected_enduser_invoice = st.selectbox(
                "Select Buyer", 
                options=get_enduser_dropdown_options(),
                key="enduser_dropdown_invoice"
            )
            
            if selected_enduser_invoice and selected_enduser_invoice != "Select End User":
                enduser_data = END_USER_DATABASE.get(selected_enduser_invoice, {})
                st.session_state.invoice_buyer_company = selected_enduser_invoice
                st.session_state.invoice_buyer_address = enduser_data.get("address", "")
                st.session_state.invoice_buyer_mobile = enduser_data.get("mobile", "")
                st.session_state.invoice_buyer_email = enduser_data.get("email", "")
                st.session_state.invoice_buyer_gst = enduser_data.get("gst_no", "")
            
            buyer_name = st.text_input(
                "Buyer Name",
                value=st.session_state.get("invoice_buyer_company", "Customer Company Ltd."),
                key="invoice_buyer_company"
            )
            
            buyer_address = st.text_area(
                "Buyer Address",
                value=st.session_state.get("invoice_buyer_address", "Customer Address"),
                key="invoice_buyer_address"
            )

            buyer_mobile = st.text_input(
                "Buyer mobile.",
                value=st.session_state.get("invoice_buyer_mobile", "00000 00000"),
                key="invoice_buyer_mobile"
            )
            buyer_email = st.text_input(
                "Buyer email.",
                value=st.session_state.get("invoice_buyer_email", "customer@company.com"),
                key="invoice_buyer_email"
            )
            buyer_gst = st.text_input(
                "Buyer GST No.",
                value=st.session_state.get("invoice_buyer_gst", "GSTNUMBER"),
                key="invoice_buyer_gst"
            )

            st.subheader("Products")
            items = []
            num_items = st.number_input("Number of Products", 1, 10, 1, key="invoice_num_items")
            for i in range(num_items):
                with st.expander(f"Product {i+1}"):
                    desc = st.text_area(f"Description {i+1}", "Software Product\nDescription\nSerial #\nContract #\nEnd Date:", key=f"invoice_desc_{i}")
                    hsn = st.text_input(f"HSN/SAC {i+1}", "997331", key=f"invoice_hsn_{i}")
                    qty = st.number_input(f"Quantity {i+1}", 1.00, 100.00, 1.00, key=f"invoice_qty_{i}")
                    rate = st.number_input(f"Unit Rate {i+1}", 0.00, 100000000.00, 10000.00, key=f"invoice_rate_{i}")
                    rate = round(rate, 2)
                    items.append({"description": desc, "hsn": hsn, "quantity": qty, "unit_rate": rate})

            st.subheader("Declaration")
            declaration = st.text_area("Declaration", "Standard declaration text as per your requirements.")
            
            st.subheader("Company Branding")
            st.info("Using global logo and stamp from sidebar settings")
            logo_path = global_logo_path
            stamp_path = global_stamp_path

            if not logo_path:
                st.warning("⚠ No company logo available")
            if not stamp_path:
                st.warning("⚠ No company stamp available")
            
            st.subheader("Invoice Preview & Download")

            if st.button("Generate Invoice", key="generate_invoice_button"):
                current_invoice_no = st.session_state.invoice_number
                
                try:
                    prefix, year_range, quarter, sequence = parse_invoice_number(current_invoice_no)
                    manual_sequence = int(sequence)
                    
                    with open(INVOICE_COUNTER_FILE, 'w') as f:
                        f.write(str(manual_sequence))
                    
                    st.session_state.invoice_seq = manual_sequence
                    
                    st.success(f"✅ Invoice sequence updated to: {manual_sequence}")
                    
                except Exception as e:
                    st.error(f"Error parsing invoice number: {e}")
                
                invoice_no = current_invoice_no
                
                basic_amount = round(sum(item['quantity'] * item['unit_rate'] for item in items), 2)
                sgst = round(basic_amount * 0.09, 2)
                cgst = round(basic_amount * 0.09, 2)
                final_amount_unrounded = basic_amount + sgst + cgst
                
                final_amount = round(final_amount_unrounded)
                round_off = final_amount - final_amount_unrounded
                
                st.info(f"**Calculated Amounts:** Basic: ₹{basic_amount:.2f}, SGST: ₹{sgst:.2f}, CGST: ₹{cgst:.2f}, Final: ₹{final_amount:.2f}")
                if round_off != 0:
                    st.info(f"**Round Off:** ₹{round_off:.2f}")
                
                def convert_to_indian_currency(amount):
                    try:
                        rupees = int(amount)
                        paise = round((amount - rupees) * 100)
                        
                        rupees_text = num2words(rupees, to='cardinal', lang='en_IN').title()
                        
                        if paise > 0:
                            paise_text = num2words(paise, to='cardinal', lang='en_IN').title()
                            return f"{rupees_text} Rupees And {paise_text} Paise Only/-"
                        else:
                            return f"{rupees_text} Rupees Only/-"
                            
                    except Exception as e:
                        return f"Amount: ₹{amount:.2f}"

                amount_in_words = convert_to_indian_currency(final_amount)
                tax_in_words = convert_to_indian_currency(round(sgst + cgst, 2))

                invoice_data = {
                    "invoice": {"invoice_no": invoice_no, "date": invoice_date},
                    "Reference": {"Suppliers_Reference": Suppliers_Reference, "Other": Others_Reference},
                    "vendor": {"name": vendor_name, "address": vendor_address, "gst": vendor_gst, "msme": vendor_msme},
                    "buyer": {"name": buyer_name, "address": buyer_address, "gst": buyer_gst, "mobile":buyer_mobile, "email":buyer_email},
                    "invoice_details": {
                        "buyers_order_no": buyers_order_no,
                        "buyers_order_date": buyers_order_date,
                        "dispatched_through": dispatched_through,
                        "payment_terms": payment_terms,
                        "terms_of_delivery": terms_of_delivery,
                        "destination": destination
                    },
                    "items": items,
                    "totals": {
                        "basic_amount": basic_amount,
                        "sgst": sgst,
                        "cgst": cgst,
                        "final_amount": final_amount,
                        "amount_in_words": amount_in_words,
                        "tax_in_words": tax_in_words
                    },
                    "declaration": declaration
                }

                pdf_file = create_invoice_pdf(invoice_data, logo_path, stamp_path)

                st.session_state.last_invoice_number = invoice_no
                
                if invoice_auto_increment:
                    next_sequence = manual_sequence + 1
                    st.session_state.invoice_seq = next_sequence
                    
                    with open(INVOICE_COUNTER_FILE, 'w') as f:
                        f.write(str(next_sequence))

                st.success("Invoice generated successfully!")
                
                st.download_button(
                    "⬇ Download Invoice PDF",
                    data=pdf_file,
                    file_name=f"{buyer_name}_{invoice_date}_{invoice_no.replace('/', '_')}.pdf",
                    mime="application/pdf",
                    key="invoice_download_button")
                                
for path in ["github_logo.jpg", "github_stamp.jpg", "custom_logo.jpg", "custom_stamp.jpg"]:
    if os.path.exists(path):
        try:
            os.remove(path)
        except:
            pass

st.divider()
st.caption("© 2025 Document Generator")

if __name__ == "__main__":
    main()



