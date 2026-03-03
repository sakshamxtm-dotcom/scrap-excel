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
    st.error("SYSTEM ERROR: Missing libraries. Please add 'fpdf', 'openpyxl', and 'pandas' to requirements.txt.")

# --- CREDENTIALS ---
USER_EMAIL = "saksham.xtm@gmail.com"
APP_PASSWORD = "up78ex2121" 

SAVE_FOLDER = "scrap_data_logs" 
MASTER_FILE = f"SCRAP_Master_{datetime.now().strftime('%m_%Y')}.xlsx"
FULL_MASTER_PATH = os.path.join(SAVE_FOLDER, MASTER_FILE)

if not os.path.exists(SAVE_FOLDER):
    os.makedirs(SAVE_FOLDER)

st.set_page_config(page_title="SCRAP MAIN SERVER", layout="wide", page_icon="🏢")

# --- PARTY PRESETS ---
PARTY_LIST = ["Select Party", "Ganesh Steel", "RK Industries", "Modern Scrap", "City Traders", "Other (Type Below)"]

# --- PDF ENGINE (LANDSCAPE) ---
class SCRAP_PDF(FPDF):
    def header(self):
        self.set_fill_color(220, 220, 220)
        self.set_font('Arial', 'B', 18)
        self.cell(0, 15, 'SCRAP (Main Server)', 1, 1, 'C', 1)
        self.set_font('Arial', 'I', 10)
        self.cell(0, 8, f'Official Transaction Ledger | {datetime.now().strftime("%d/%m/%Y")}', 0, 1, 'C')
        self.ln(5)

def generate_pro_pdf(df, date_label):
    pdf = SCRAP_PDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 7)
    
    cols = {
        "Date": 22, "Vehicle": 28, "Party": 35, "Location": 25, 
        "W.Qty": 18, "G.Qty": 18, "P.Rate": 18, "M.Rate": 18,
        "Report": 22, "Purch": 22, "Saving": 28
    }
    
    for title, width in cols.items():
        pdf.cell(width, 10, title, 1, 0, 'C', 1)
    pdf.ln()

    pdf.set_font("Arial", '', 7)
    grand_total = 0
    for _, row in df.iterrows():
        d = row['Date'] if isinstance(row['Date'], str) else row['Date'].strftime('%d/%m/%Y')
        pdf.cell(cols["Date"], 10, d, 1)
        pdf.cell(cols["Vehicle"], 10, str(row['Vehicle No']), 1)
        pdf.cell(cols["Party"], 10, str(row['Party Name']), 1)
        pdf.cell(cols["Location"], 10, str(row['Location']), 1)
        pdf.cell(cols["W.Qty"], 10, str(row['White Scrap (Qty)']), 1)
        pdf.cell(cols["G.Qty"], 10, str(row['Green Scrap (Qty)']), 1)
        pdf.cell(cols["P.Rate"], 10, str(row['Party Rate']), 1)
        pdf.cell(cols["M.Rate"], 10, str(row['Mill Rate']), 1)
        pdf.cell(cols["Report"], 10, f"{float(row['Report']):,.0f}", 1)
        pdf.cell(cols["Purch"], 10, f"{float(row['Purchase']):,.0f}", 1)
        
        s_val = float(row['Total Saving'])
        pdf.cell(cols["Saving"], 10, f"{s_val:,.2f}", 1)
        grand_total += s_val
        pdf.ln()

    pdf.ln(5)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 10, f"GRAND TOTAL NET SAVING: INR {grand_total:,.2f}", 0, 1, 'R')
    
    fn = f"SCRAP_Server_Report_{date_label.replace('/','-')}.pdf"
    pdf.output(fn)
    return fn

# --- MAIL ENGINE ---
def send_secure_email(file_path):
    try:
        msg = MIMEMultipart()
        msg['From'], msg['To'] = USER_EMAIL, USER_EMAIL
        msg['Subject'] = f"SCRAP MAIN SERVER: {datetime.now().strftime('%d/%m/%Y')}"
        msg.attach(MIMEText("SCRAP (Main Server) secure transaction data attached.", 'plain'))
        with open(file_path, "rb") as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f"attachment; filename= {os.path.basename(file_path)}")
            msg.attach(part)
        s = smtplib.SMTP('smtp.gmail.com', 587); s.starttls()
        s.login(USER_EMAIL, APP_PASSWORD); s.send_message(msg); s.quit()
        return True
    except Exception as e:
        st.error(f"Mail Delivery Failed: {e}"); return False

# --- UI LOGIC ---
if 'entries' not in st.session_state:
    st.session_state.entries = [0]

def add_vehicle_row():
    st.session_state.entries.append(len(st.session_state.entries))

st.title("🏗️ SCRAP (Main Server)")

processed_rows = []
for i in st.session_state.entries:
    with st.expander(f"🚛 Vehicle Entry #{i+1}", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        sel_party = c1.selectbox("Party Selection", options=PARTY_LIST, key=f"sel_{i}")
        p_name = c1.text_input("Manual Party Entry", key=f"man_{i}") if sel_party in ["Select Party", "Other (Type Below)"] else sel_party
        loc, v_no = c2.text_input("Location", key=f"loc_{i}"), c3.text_input("Vehicle No", key=f"vno_{i}")
        rev = c4.number_input("Total Revenue", value=None, format="%.2f", key=f"rev_{i}")
        
        c5, c6, c7, c8 = st.columns(4)
        wq, gq, pr, mr = c5.number_input("White Qty", value=None, key=f"wq_{i}"), c6.number_input("Green Qty", value=None, key=f"gq_{i}"), c7.number_input("Party Rate", value=None, key=f"pr_{i}"), c8.number_input("Mill Rate", value=None, key=f"mr_{i}")
        
        c9, c10, c11 = st.columns(3)
        rep, pur, ch = c9.number_input("Report Amount", value=None, key=f"rep_{i}"), c10.number_input("Purchase Amount", value=None, key=f"pur_{i}"), c11.number_input("Vehicle Charge", value=None, key=f"ch_{i}")

        # --- DYNAMIC GST INPUTS ---
        cg1, cg2 = st.columns(2)
        gst_p_pct = cg1.number_input("GST Purchase %", value=5.0, key=f"gp_pct_{i}")
        gst_s_pct = cg2.number_input("GST Sale %", value=18.0, key=f"gs_pct_{i}")

        # --- GST CALCULATION ---
        revenue_val = rev if rev else 0.0
        purchase_val = pur if pur else 0.0
        report_val = rep if rep else 0.0
        charge_val = ch if ch else 0.0
        
        gst_p_amt = revenue_val * (gst_p_pct / 100)
        gst_s_amt = revenue_val * (gst_s_pct / 100)
        
        net_saving = (purchase_val - report_val - charge_val) + gst_p_amt + gst_s_amt
        
        st.success(f"Calculated Saving: ₹ {net_saving:,.2f}")
        
        processed_rows.append({
            "Date": date.today().strftime("%d/%m/%Y"), "Party Name": p_name, "Location": loc,
            "Vehicle No": v_no, "Revenue": revenue_val, "White Scrap (Qty)": wq if wq else 0,
            "Green Scrap (Qty)": gq if gq else 0, "Party Rate": pr if pr else 0,
            "Mill Rate": mr if mr else 0, "Report": report_val, "Purchase": purchase_val,
            "Vehicle Charge": charge_val, "Total Saving": net_saving
        })

if st.button("➕ Add Next Vehicle", use_container_width=True):
    add_vehicle_row()
    st.rerun()

st.divider()
col_sync, col_pdf = st.columns(2)

with col_sync:
    if st.button("🚀 SYNC DATA & EMAIL SERVER", type="primary", use_container_width=True):
        df_final = pd.DataFrame(processed_rows)
        if os.path.exists(FULL_MASTER_PATH):
            df_final = pd.concat([pd.read_excel(FULL_MASTER_PATH), df_final], ignore_index=True)
        df_final.to_excel(FULL_MASTER_PATH, index=False)
        pdf_path = generate_pro_pdf(pd.DataFrame(processed_rows), date.today().strftime("%d-%m-%Y"))
        if send_secure_email(pdf_path):
            st.toast("Success: Server Updated!", icon="✅")

with col_pdf:
    if st.button("📄 Generate Today's PDF", use_container_width=True):
        today_pdf = generate_pro_pdf(pd.DataFrame(processed_rows), f"Today_{date.today().strftime('%d-%m-%Y')}")
        with open(today_pdf, "rb") as f:
            st.download_button("📥 Click to Download PDF", f, file_name=today_pdf, use_container_width=True)
