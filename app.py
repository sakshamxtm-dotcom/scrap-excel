import streamlit as st
import pandas as pd
from datetime import datetime
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# --- LIBRARY CHECK ---
try:
    from fpdf import FPDF
except ImportError:
    st.error("Please add 'fpdf' and 'openpyxl' to your requirements.txt file.")

# --- CREDENTIALS ---
USER_EMAIL = "lakshya.pcvn@gmail.com"
APP_PASSWORD = "soelepugugonpaua" 

# --- FOLDER SETUP ---
SAVE_FOLDER = "scrap_data_logs" 
if not os.path.exists(SAVE_FOLDER):
    os.makedirs(SAVE_FOLDER)

st.set_page_config(page_title="SCRAP PRO", layout="wide", page_icon="🏗️")

# --- PDF GENERATOR (LANDSCAPE FOR ALL COLUMNS) ---
class SCRAP_PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'SCRAP INDUSTRIAL DAILY LEDGER', 0, 1, 'C')
        self.set_font('Arial', '', 10)
        self.cell(0, 5, f'Date: {datetime.now().strftime("%d-%b-%Y")}', 0, 1, 'C')
        self.ln(10)

def generate_pro_pdf(df, total_sav):
    # 'L' for Landscape to fit all columns
    pdf = SCRAP_PDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 8)
    
    # Define Column Widths (Total 280mm for Landscape A4)
    cols = {
        "Vehicle": 30, "Party": 40, "Revenue": 25, 
        "W.Scrap": 20, "G.Scrap": 20, "P.Rate": 20, 
        "M.Rate": 20, "Report": 25, "Purch": 25, 
        "Charge": 25, "Saving": 30
    }

    # Draw Header
    for title, width in cols.items():
        pdf.cell(width, 10, title, 1, 0, 'C')
    pdf.ln()

    # Draw Rows
    pdf.set_font("Arial", '', 8)
    for _, row in df.iterrows():
        pdf.cell(cols["Vehicle"], 10, str(row['Vehicle No'] or ""), 1)
        pdf.cell(cols["Party"], 10, str(row['Party Name'] or ""), 1)
        pdf.cell(cols["Revenue"], 10, str(row['Revenue'] or "0"), 1)
        pdf.cell(cols["W.Scrap"], 10, str(row['White Scrap (Qty)'] or "0"), 1)
        pdf.cell(cols["G.Scrap"], 10, str(row['Green Scrap (Qty)'] or "0"), 1)
        pdf.cell(cols["P.Rate"], 10, str(row['Party Rate'] or "0"), 1)
        pdf.cell(cols["M.Rate"], 10, str(row['Mill Rate'] or "0"), 1)
        pdf.cell(cols["Report"], 10, str(row['Report'] or "0"), 1)
        pdf.cell(cols["Purch"], 10, str(row['Purchase'] or "0"), 1)
        pdf.cell(cols["Charge"], 10, str(row['Vehicle Charge'] or "0"), 1)
        pdf.cell(cols["Saving"], 10, f"{row['Total Saving']:,.2f}", 1)
        pdf.ln()

    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"TOTAL NET SAVINGS: INR {total_sav:,.2f}", 0, 1, 'R')
    
    file_name = f"Full_Report_{datetime.now().strftime('%d_%m_%Y')}.pdf"
    pdf.output(file_name)
    return file_name

# --- APP LOGIC ---
if 'rows' not in st.session_state:
    st.session_state.rows = [{
        'Date': datetime.now().strftime('%d-%m-%Y'),
        'Party Name': '', 'Location': '', 'Vehicle No': '', 
        'Revenue': None, 'White Scrap (Qty)': None, 'Green Scrap (Qty)': None,
        'Party Rate': None, 'Mill Rate': None, 'Report': None, 
        'Purchase': None, 'Vehicle Charge': None, 
        'GST Purchase %': 18.0, 'GST Sale %': 18.0, 'Total Saving': 0.0
    }]

st.title("🏗️ SCRAP PRO - Master Control")
st.info("Fill all columns. The PDF and Excel will now include every detail.")

total_daily_saving = 0.0

for i, row in enumerate(st.session_state.rows):
    with st.expander(f"🚛 Vehicle Entry #{i+1}", expanded=True):
        # Row 1
        c1, c2, c3, c4 = st.columns(4)
        row['Party Name'] = c1.text_input("Party Name", value=row['Party Name'], key=f"p_{i}")
        row['Location'] = c2.text_input("Location", value=row['Location'], key=f"l_{i}")
        row['Vehicle No'] = c3.text_input("Vehicle No", value=row['Vehicle No'], key=f"v_{i}")
        row['Revenue'] = c4.number_input("Total Revenue", value=row['Revenue'], key=f"r_{i}")

        # Row 2
        c5, c6, c7, c8 = st.columns(4)
        row['White Scrap (Qty)'] = c5.number_input("White Scrap Qty", value=row['White Scrap (Qty)'], key=f"ws_{i}")
        row['Green Scrap (Qty)'] = c6.number_input("Green Scrap Qty", value=row['Green Scrap (Qty)'], key=f"gs_{i}")
        row['Party Rate'] = c7.number_input("Party Rate", value=row['Party Rate'], key=f"pr_{i}")
        row['Mill Rate'] = c8.number_input("Mill Rate", value=row['Mill Rate'], key=f"mr_{i}")

        # Row 3
        c9, c10, c11, c12 = st.columns(4)
        row['Report'] = c9.number_input("Report Amt", value=row['Report'], key=f"rep_{i}")
        row['Purchase'] = c10.number_input("Purchase Amt", value=row['Purchase'], key=f"pur_{i}")
        row['Vehicle Charge'] = c11.number_input("Vehicle Charge", value=row['Vehicle Charge'], key=f"vc_{i}")
        
        # GST Split
        gst_p_pct = c12.number_input("GST Purchase %", value=row['GST Purchase %'], key=f"gpp_{i}")
        gst_s_pct = st.number_input("GST Sale %", value=row['GST Sale %'], key=f"gsp_{i}")
        
        # Calculation
        gst_p = (row['Revenue'] or 0) * (gst_p_pct / 100)
        gst_s = (row['Revenue'] or 0) * (gst_s_pct / 100)
        row['Total Saving'] = ((row['Purchase'] or 0) - (row['Report'] or 0) - (row['Vehicle Charge'] or 0)) + gst_p + gst_s
        total_daily_saving += row['Total Saving']

# --- FOOTER ACTIONS ---
st.write("---")
col_add, col_save = st.columns(2)

with col_add:
    if st.button("➕ Add Another Vehicle", use_container_width=True):
        st.session_state.rows.append({'Date': datetime.now().strftime('%d-%m-%Y'), 'Party Name': '', 'Location': '', 'Vehicle No': '', 'Revenue': None, 'White Scrap (Qty)': None, 'Green Scrap (Qty)': None, 'Party Rate': None, 'Mill Rate': None, 'Report': None, 'Purchase': None, 'Vehicle Charge': None, 'GST Purchase %': 18.0, 'GST Sale %': 18.0, 'Total Saving': 0.0})
        st.rerun()

with col_save:
    if st.button("🚀 SYNC EXCEL & GENERATE FULL PDF", type="primary", use_container_width=True):
        df = pd.DataFrame(st.session_state.rows)
        
        # 1. Update Monthly Excel (All 12+ Columns)
        month_name = f"SCRAP_Master_{datetime.now().strftime('%B_%Y')}.xlsx"
        path = os.path.join(SAVE_FOLDER, month_name)
        if os.path.exists(path):
            existing = pd.read_excel(path)
            df_final = pd.concat([existing, df], ignore_index=True)
        else:
            df_final = df
        df_final.to_excel(path, index=False)
        
        # 2. Generate Landscape PDF
        pdf_file = generate_pro_pdf(df, total_daily_saving)
        
        st.balloons()
        st.success(f"Master Excel Updated: {month_name}")
        with open(pdf_file, "rb") as f:
            st.download_button("📥 Download Full Landscape PDF Report", f, file_name=pdf_file)

# --- MASTER VIEW ---
with st.expander("📊 View All Rows Preview"):
    st.dataframe(pd.DataFrame(st.session_state.rows))
