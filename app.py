import streamlit as st
import pandas as pd
from datetime import datetime
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Try-Except block to handle the library issue gracefully
try:
    from fpdf import FPDF
except ImportError:
    st.error("Missing Library: Please run 'pip install fpdf' or add it to requirements.txt")

# --- CREDENTIALS ---
USER_EMAIL = "lakshya.pcvn@gmail.com"
APP_PASSWORD = "soelepugugonpaua" 

# --- FOLDER SETUP ---
SAVE_FOLDER = "scrap_data_logs" 
if not os.path.exists(SAVE_FOLDER):
    os.makedirs(SAVE_FOLDER)

st.set_page_config(page_title="SCRAP PRO", layout="wide", page_icon="🏗️")

# --- PDF GENERATOR ---
class SCRAP_PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'SCRAP BUSINESS REPORT', 0, 1, 'C')
        self.ln(5)

def generate_pdf(df, total_sav):
    pdf = SCRAP_PDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 10)
    
    # Table Headers
    cols = ["Vehicle No", "Party", "Revenue", "Saving"]
    for col in cols:
        pdf.cell(45, 10, col, 1)
    pdf.ln()

    # Table Rows
    pdf.set_font("Arial", '', 10)
    for _, row in df.iterrows():
        pdf.cell(45, 10, str(row['Vehicle No'] or "N/A"), 1)
        pdf.cell(45, 10, str(row['Party Name'] or "N/A"), 1)
        pdf.cell(45, 10, str(row['Revenue'] or "0"), 1)
        pdf.cell(45, 10, f"{row['Total Saving']:.2f}", 1)
        pdf.ln()

    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"TOTAL DAILY SAVING: INR {total_sav:,.2f}", 0, 1)
    
    pdf_file = f"Report_{datetime.now().strftime('%d_%m_%Y')}.pdf"
    pdf.output(pdf_file)
    return pdf_file

# --- APP UI ---
st.title("🏗️ SCRAP PRO")
st.write("Fill in the details below and sync to your Master Excel.")

if 'rows' not in st.session_state:
    st.session_state.rows = [{
        'Date': datetime.now().strftime('%d-%m-%Y'),
        'Party Name': '', 'Vehicle No': '', 'Revenue': None, 
        'Report': None, 'Purchase': None, 'Vehicle Charge': None, 
        'GST Purchase %': 18.0, 'GST Sale %': 18.0, 'Total Saving': 0.0
    }]

# (Input Logic same as before...)
total_daily_saving = 0.0
for i, row in enumerate(st.session_state.rows):
    with st.expander(f"🚛 Vehicle Entry #{i+1}", expanded=True):
        c1, c2, c3 = st.columns(3)
        row['Party Name'] = c1.text_input("Party", value=row['Party Name'], key=f"p_{i}")
        row['Vehicle No'] = c2.text_input("Vehicle No", value=row['Vehicle No'], key=f"v_{i}")
        row['Revenue'] = c3.number_input("Revenue", value=row['Revenue'], key=f"r_{i}")
        
        c4, c5, c6 = st.columns(3)
        row['Report'] = c4.number_input("Report", value=row['Report'], key=f"rep_{i}")
        row['Purchase'] = c5.number_input("Purchase", value=row['Purchase'], key=f"pur_{i}")
        row['Vehicle Charge'] = c6.number_input("Charge", value=row['Vehicle Charge'], key=f"vc_{i}")

        # Math logic
        gst_p = (row['Revenue'] or 0) * (row['GST Purchase %'] / 100)
        gst_s = (row['Revenue'] or 0) * (row['GST Sale %'] / 100)
        row['Total Saving'] = ((row['Purchase'] or 0) - (row['Report'] or 0) - (row['Vehicle Charge'] or 0)) + gst_p + gst_s
        total_daily_saving += row['Total Saving']

if st.button("➕ Add Row"):
    st.session_state.rows.append({'Date': datetime.now().strftime('%d-%m-%Y'), 'Party Name': '', 'Vehicle No': '', 'Revenue': None, 'Report': None, 'Purchase': None, 'Vehicle Charge': None, 'GST Purchase %': 18.0, 'GST Sale %': 18.0, 'Total Saving': 0.0})
    st.rerun()

if st.button("🚀 SAVE & GENERATE PDF", type="primary"):
    df = pd.DataFrame(st.session_state.rows)
    pdf_path = generate_pdf(df, total_daily_saving)
    
    # Update Excel
    month_file = f"SCRAP_Master_{datetime.now().strftime('%B_%Y')}.xlsx"
    filepath = os.path.join(SAVE_FOLDER, month_file)
    if os.path.exists(filepath):
        existing = pd.read_excel(filepath)
        df = pd.concat([existing, df], ignore_index=True)
    df.to_excel(filepath, index=False)
    
    st.success("Excel Updated!")
    with open(pdf_path, "rb") as f:
        st.download_button("📥 Download PDF Report", f, file_name=pdf_path)
