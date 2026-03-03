import streamlit as st
import pandas as pd
from datetime import datetime, date
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
    st.error("Please add 'fpdf', 'openpyxl', and 'pandas' to your requirements.txt.")

# --- CREDENTIALS (UPDATED) ---
USER_EMAIL = "saksham.xtm@gmail.com"
APP_PASSWORD = "up78ex2121" 

SAVE_FOLDER = "scrap_data_logs" 
MASTER_FILE = f"SCRAP_Master_{datetime.now().strftime('%B_%Y')}.xlsx"

if not os.path.exists(SAVE_FOLDER):
    os.makedirs(SAVE_FOLDER)

st.set_page_config(page_title="SCRAP MAIN SERVER", layout="wide", page_icon="🏢")

# --- PDF GENERATOR (MAIN SERVER BRANDING) ---
class SCRAP_PDF(FPDF):
    def header(self):
        self.set_fill_color(200, 220, 255)
        self.set_font('Arial', 'B', 18)
        self.cell(0, 15, 'SCRAP (Main Server)', 1, 1, 'C', 1)
        self.set_font('Arial', 'I', 10)
        self.cell(0, 8, f'Official Transaction Ledger | Generated: {datetime.now().strftime("%d-%b-%Y %H:%M")}', 0, 1, 'C')
        self.ln(10)

def generate_custom_pdf(df, title_date_range):
    pdf = SCRAP_PDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    
    # Table Config
    pdf.set_font("Arial", 'B', 8)
    cols = {"Date": 25, "Vehicle": 30, "Party": 40, "Revenue": 25, "Purch": 25, "Report": 25, "Charge": 25, "Saving": 35}
    
    for title, width in cols.items():
        pdf.cell(width, 10, title, 1, 0, 'C')
    pdf.ln()

    pdf.set_font("Arial", '', 8)
    total_sav = 0
    for _, row in df.iterrows():
        pdf.cell(cols["Date"], 10, str(row['Date']), 1)
        pdf.cell(cols["Vehicle"], 10, str(row['Vehicle No']), 1)
        pdf.cell(cols["Party"], 10, str(row['Party Name']), 1)
        pdf.cell(cols["Revenue"], 10, f"{row['Revenue']:.2f}", 1)
        pdf.cell(cols["Purch"], 10, f"{row['Purchase']:.2f}", 1)
        pdf.cell(cols["Report"], 10, f"{row['Report']:.2f}", 1)
        pdf.cell(cols["Charge"], 10, f"{row['Vehicle Charge']:.2f}", 1)
        save_val = float(row['Total Saving'])
        pdf.cell(cols["Saving"], 10, f"{save_val:,.2f}", 1)
        total_sav += save_val
        pdf.ln()

    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"TOTAL PERIOD SAVING: INR {total_sav:,.2f}", 0, 1, 'R')
    
    f_name = f"SCRAP_Report_{title_date_range}.pdf"
    pdf.output(f_name)
    return f_name

# --- EMAIL LOGIC ---
def send_email_with_pdf(file_path):
    try:
        msg = MIMEMultipart()
        msg['From'] = USER_EMAIL
        msg['To'] = USER_EMAIL
        msg['Subject'] = f"SCRAP SERVER REPORT - {datetime.now().strftime('%d %b')}"
        msg.attach(MIMEText("Attached is the requested SCRAP PDF Report from the Main Server.", 'plain'))
        
        with open(file_path, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f"attachment; filename= {os.path.basename(file_path)}")
            msg.attach(part)
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(USER_EMAIL, APP_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Mail Server Error: {e}")
        return False

# --- UI INTERFACE ---
st.title("🏗️ SCRAP (Main Server)")
st.write(f"Logged in as: **{USER_EMAIL}**")

# --- DATA INPUT SECTION ---
if 'rows' not in st.session_state:
    st.session_state.rows = []

with st.expander("➕ Create New Vehicle Entries", expanded=True):
    num_v = st.number_input("How many vehicles today?", min_value=1, step=1, value=1)
    
    current_entries = []
    for i in range(num_v):
        st.markdown(f"**Vehicle #{i+1}**")
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        p_name = c1.text_input("Party", key=f"p{i}")
        v_no = c2.text_input("Vehicle No", key=f"v{i}")
        rev = c3.number_input("Revenue", key=f"r{i}")
        pur = c4.number_input("Purchase", key=f"pur{i}")
        rep = c5.number_input("Report", key=f"rep{i}")
        chrg = c6.number_input("Charge", key=f"ch{i}")
        
        # Calculation (Simplified for UI, uses split GST internally if needed)
        # Based on previous logic: (Purchase - Report - Charge) + 36% (18+18) of Revenue
        gst_amt = rev * 0.36
        saving = (pur - rep - chrg) + gst_amt
        
        current_entries.append({
            "Date": date.today().strftime("%Y-%m-%d"),
            "Party Name": p_name, "Vehicle No": v_no, "Revenue": rev,
            "Purchase": pur, "Report": rep, "Vehicle Charge": chrg, "Total Saving": saving
        })

# --- PDF ACTION BUTTONS ---
st.write("---")
col_today, col_range = st.columns(2)

with col_today:
    st.subheader("📅 Today's Report")
    if st.button("🚀 Generate Today's PDF & Send Mail", use_container_width=True):
        today_df = pd.DataFrame(current_entries)
        
        # Update Master Excel
        path = os.path.join(SAVE_FOLDER, MASTER_FILE)
        if os.path.exists(path):
            old_df = pd.read_excel(path)
            today_df = pd.concat([old_df, today_df], ignore_index=True)
        today_df.to_excel(path, index=False)
        
        # Generate PDF
        pdf_file = generate_custom_pdf(pd.DataFrame(current_entries), date.today().strftime("%d-%b-%Y"))
        if send_email_with_pdf(pdf_file):
            st.success(f"Sent to {USER_EMAIL}")
            st.balloons()
            with open(pdf_file, "rb") as f:
                st.download_button("📥 Download Today's PDF", f, file_name=pdf_file)

with col_range:
    st.subheader("🔍 Historical Report")
    d1 = st.date_input("Start Date", value=date.today())
    d2 = st.date_input("End Date", value=date.today())
    
    if st.button("🔎 Filter & Generate Range PDF", use_container_width=True):
        path = os.path.join(SAVE_FOLDER, MASTER_FILE)
        if os.path.exists(path):
            master_df = pd.read_excel(path)
            master_df['Date'] = pd.to_datetime(master_df['Date']).dt.date
            mask = (master_df['Date'] >= d1) & (master_df['Date'] <= d2)
            filtered_df = master_df.loc[mask]
            
            if not filtered_df.empty:
                range_pdf = generate_custom_pdf(filtered_df, f"{d1}_to_{d2}")
                st.success(f"Report Generated for {len(filtered_df)} vehicles.")
                with open(range_pdf, "rb") as f:
                    st.download_button("📥 Download Range PDF", f, file_name=range_pdf)
            else:
                st.error("No data found for these dates.")
        else:
            st.error("No Master Ledger found. Save today's data first!")
