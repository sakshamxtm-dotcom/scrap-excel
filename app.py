import streamlit as st
import pandas as pd
from datetime import datetime
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from fpdf import FPDF # New: For PDF Generation

# --- CREDENTIALS ---
USER_EMAIL = "lakshya.pcvn@gmail.com"
APP_PASSWORD = "soelepugugonpaua" 

# --- FOLDER SETUP ---
SAVE_FOLDER = "scrap_data_logs" 
if not os.path.exists(SAVE_FOLDER):
    os.makedirs(SAVE_FOLDER)

st.set_page_config(page_title="SCRAP PRO", layout="wide", page_icon="🏗️")

# --- PDF GENERATOR FUNCTION ---
class SCRAP_PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'SCRAP BUSINESS REPORT', 0, 1, 'C')
        self.set_font('Arial', '', 10)
        self.cell(0, 10, f'Generated on: {datetime.now().strftime("%d-%b-%Y %H:%M")}', 0, 1, 'R')
        self.ln(10)

def generate_pdf(df, filename, total_sav):
    pdf = SCRAP_PDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 12)
    
    # Header Row
    pdf.cell(40, 10, "Vehicle No", 1)
    pdf.cell(50, 10, "Party Name", 1)
    pdf.cell(40, 10, "Revenue", 1)
    pdf.cell(40, 10, "Net Saving", 1)
    pdf.ln()

    pdf.set_font("Arial", '', 10)
    for index, row in df.iterrows():
        pdf.cell(40, 10, str(row['Vehicle No']), 1)
        pdf.cell(50, 10, str(row['Party Name']), 1)
        pdf.cell(40, 10, f"{row['Revenue']:,.2f}", 1)
        pdf.cell(40, 10, f"{row['Total Saving']:,.2f}", 1)
        pdf.ln()

    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"GRAND TOTAL SAVING: INR {total_sav:,.2f}", 0, 1, 'L')
    
    pdf_output = filename.replace(".xlsx", ".pdf")
    pdf.output(pdf_output)
    return pdf_output

# --- HEADER & CLOCK ---
col_title, col_clock = st.columns([3, 1])
with col_title:
    st.title("🏗️ SCRAP PRO")
    st.markdown(f"#### *Advanced Logistics & Financial Summary*")
with col_clock:
    now = datetime.now()
    st.metric(label=now.strftime("%B %Y"), value=now.strftime("%d %a"), delta=now.strftime("%H:%M:%S"))

# --- SESSION STATE ---
if 'rows' not in st.session_state:
    st.session_state.rows = [{
        'Date': datetime.now().strftime('%d-%m-%Y'),
        'Party Name': '', 'Location': '', 'Vehicle No': '', 
        'Revenue': None, 'White Scrap (Qty)': None, 'Green Scrap (Qty)': None,
        'Party Rate': None, 'Mill Rate': None, 'Report': None, 
        'Purchase': None, 'Vehicle Charge': None, 
        'GST Purchase %': 18.0, 'GST Sale %': 18.0, 'Total Saving': 0.0
    }]

def add_row():
    st.session_state.rows.append({
        'Date': datetime.now().strftime('%d-%m-%Y'),
        'Party Name': '', 'Location': '', 'Vehicle No': '', 
        'Revenue': None, 'White Scrap (Qty)': None, 'Green Scrap (Qty)': None,
        'Party Rate': None, 'Mill Rate': None, 'Report': None, 
        'Purchase': None, 'Vehicle Charge': None, 
        'GST Purchase %': 18.0, 'GST Sale %': 18.0, 'Total Saving': 0.0
    })

# --- UI INPUT AREA ---
st.write("---")
total_daily_saving = 0.0

for i, row in enumerate(st.session_state.rows):
    with st.container():
        st.markdown(f"### 🚛 Entry #{i+1}")
        c1, c2, c3, c4 = st.columns(4)
        row['Party Name'] = c1.text_input("Party Name", value=row['Party Name'], key=f"p_{i}")
        row['Vehicle No'] = c3.text_input("Vehicle Number", value=row['Vehicle No'], key=f"v_{i}")
        row['Revenue'] = c4.number_input("Total Revenue", value=row['Revenue'], key=f"r_{i}")
        
        # Financials and GST (Logic remains same as previous request)
        r3_c1, r3_c2, r3_c3 = st.columns(3)
        row['Report'] = r3_c1.number_input("Report Amount", value=row['Report'], key=f"rep_{i}")
        row['Purchase'] = r3_c2.number_input("Purchase Amount", value=row['Purchase'], key=f"pur_{i}")
        row['Vehicle Charge'] = r3_c3.number_input("Vehicle Charge", value=row['Vehicle Charge'], key=f"vc_{i}")

        gst_p_amt = (row['Revenue'] or 0) * (row['GST Purchase %'] / 100)
        gst_s_amt = (row['Revenue'] or 0) * (row['GST Sale %'] / 100)
        row['Total Saving'] = ((row['Purchase'] or 0) - (row['Report'] or 0) - (row['Vehicle Charge'] or 0)) + gst_p_amt + gst_s_amt
        total_daily_saving += row['Total Saving']
        st.divider()

# --- ACTIONS ---
st.metric("Total Daily Savings", f"₹ {total_daily_saving:,.2f}")

if st.button("🚀 SAVE, SYNC & GENERATE PDF", type="primary", use_container_width=True):
    df = pd.DataFrame(st.session_state.rows)
    
    # 1. Update Excel
    month_file = f"SCRAP_Master_{datetime.now().strftime('%B_%Y')}.xlsx"
    filepath = os.path.join(SAVE_FOLDER, month_file)
    if os.path.exists(filepath):
        existing_df = pd.read_excel(filepath)
        df = pd.concat([existing_df, df], ignore_index=True)
    df.to_excel(filepath, index=False)
    
    # 2. Generate PDF
    pdf_path = generate_pdf(pd.DataFrame(st.session_state.rows), filepath, total_daily_saving)
    
    # 3. Success Feedback
    st.balloons()
    st.success(f"Verified: Excel updated & PDF generated at {pdf_path}")
    
    # Download Button for PDF
    with open(pdf_path, "rb") as f:
        st.download_button("📥 Download PDF Report", data=f, file_name=os.path.basename(pdf_path))
      
