import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# --- SYSTEM CONSTANTS ---
USER_EMAIL = "saksham.xtm@gmail.com"
APP_PASSWORD = "iqpz gprg zbnv kfam" 
SAVE_FOLDER = "scrap_data_logs" 
MASTER_FILE = f"SCRAP_Master_{datetime.now().strftime('%m_%Y')}.xlsx"
FULL_MASTER_PATH = os.path.join(SAVE_FOLDER, MASTER_FILE)

if not os.path.exists(SAVE_FOLDER):
    os.makedirs(SAVE_FOLDER)

st.set_page_config(page_title="SCRAP MAIN SERVER", layout="wide", page_icon="🏢")

# --- PDF ENGINE ---
try:
    from fpdf import FPDF
except ImportError:
    st.error("Missing library: Install fpdf")

class SCRAP_PDF(FPDF):
    def header(self):
        self.set_fill_color(230, 230, 230) 
        self.set_text_color(0, 0, 0)       
        self.set_font('Arial', 'B', 18)
        self.cell(0, 15, 'SCRAP (Main Server)', 1, 1, 'C', 1)
        self.set_font('Arial', 'I', 10)
        self.cell(0, 8, f'Official Ledger | {datetime.now().strftime("%d/%m/%Y")}', 0, 1, 'C')
        self.ln(5)

def generate_report(df, label):
    pdf = SCRAP_PDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 8)
    pdf.set_fill_color(240, 240, 240) 
    cols = {"Date": 22, "Vehicle": 28, "Party": 40, "Location": 25, "W.Qty": 18, "G.Qty": 18, "P.Rate": 18, "M.Rate": 18, "Report": 22, "Purch": 22, "Saving": 28}
    for title, width in cols.items():
        pdf.cell(width, 10, title, 1, 0, 'C', 1) 
    pdf.ln()
    pdf.set_font("Arial", '', 7)
    total_sav = 0
    for _, row in df.iterrows():
        d_str = row['Date'] if isinstance(row['Date'], str) else row['Date'].strftime('%d/%m/%Y')
        pdf.cell(22, 10, d_str, 1)
        pdf.cell(28, 10, str(row['Vehicle No']), 1)
        pdf.cell(40, 10, str(row['Party Name'])[:25], 1) 
        pdf.cell(25, 10, str(row['Location']), 1)
        pdf.cell(18, 10, str(row['White Scrap (Qty)']), 1)
        pdf.cell(18, 10, str(row['Green Scrap (Qty)']), 1)
        pdf.cell(18, 10, str(row['Party Rate']), 1)
        pdf.cell(18, 10, str(row['Mill Rate']), 1)
        pdf.cell(22, 10, f"{float(row['Report']):,.0f}", 1)
        pdf.cell(22, 10, f"{float(row['Purchase']):,.0f}", 1)
        pdf.cell(28, 10, f"{float(row['Total Saving']):,.2f}", 1)
        total_sav += float(row['Total Saving'])
        pdf.ln()
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 11); pdf.cell(0, 10, f"TOTAL NET SAVING: INR {total_sav:,.2f}", 0, 1, 'R')
    fn = f"SCRAP_Report_{label.replace('/','-')}.pdf"
    pdf.output(fn); return fn

# --- MAIL ENGINE ---
def send_to_server(file_path):
    try:
        msg = MIMEMultipart()
        msg['From'], msg['To'] = USER_EMAIL, USER_EMAIL
        msg['Subject'] = f"SCRAP SYNC: {datetime.now().strftime('%d/%m/%Y')}"
        msg.attach(MIMEText("SCRAP Main Server Data Sync.", 'plain'))
        with open(file_path, "rb") as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read()); encoders.encode_base64(part)
            part.add_header('Content-Disposition', f"attachment; filename= {os.path.basename(file_path)}")
            msg.attach(part)
        s = smtplib.SMTP('smtp.gmail.com', 587, timeout=20)
        s.starttls(); s.login(USER_EMAIL, APP_PASSWORD); s.send_message(msg); s.quit()
        return True, "Success"
    except Exception as e: return False, str(e)

# --- UI LOGIC ---
st.title("🏗️ SCRAP (Main Server)")

if 'rows_count' not in st.session_state:
    st.session_state.rows_count = 1

daily_cache = []

for i in range(st.session_state.rows_count):
    st.subheader(f"🚛 Vehicle Entry #{i+1}")
    
    r1c1, r1c2 = st.columns(2)
    p_name = r1c1.text_input("Party Name", key=f"mn_{i}")
    loc = r1c2.text_input("Location", key=f"lc_{i}")
    v_no = r1c2.text_input("Vehicle No", key=f"vn_{i}")
    
    r2c1, r2c2, r2c3, r2c4 = st.columns(4)
    wq = r2c1.number_input("White Qty", value=None, key=f"wq_{i}")
    gq = r2c2.number_input("Green Qty", value=None, key=f"gq_{i}")
    pr = r2c3.number_input("Party Rate", value=None, key=f"pr_{i}")
    mr = r2c4.number_input("Mill Rate", value=None, key=f"mr_{i}")
    
    # Logic with empty-check
    total_qty = (wq or 0.0) + (gq or 0.0)
    auto_rev = (pr or 0.0) * total_qty
    auto_pur = ((mr or 0.0) - (pr or 0.0)) * total_qty
    
    r3c1, r3c2, r3c3, r3c4 = st.columns(4)
    st.info(f"Auto Revenue: ₹ {auto_rev:,.2f}")
    st.info(f"Auto Purchase: ₹ {auto_pur:,.2f}")
    
    rep = r3c1.number_input("Report Amount", value=None, key=f"rp_{i}")
    ch = r3c2.number_input("Vehicle Charge", value=None, key=f"ch_{i}")
    
    # GST Fields with Default Values
    gst_p = r3c3.number_input("GST Purchase %", value=5.0, key=f"gp_{i}")
    gst_s = r3c4.number_input("GST Sale %", value=18.0, key=f"gs_{i}")

    # Exclusive GST calculation logic
    saving = (auto_pur - (rep or 0.0) - (ch or 0.0)) + (auto_rev * ((gst_p or 0.0)/100)) + (auto_rev * ((gst_s or 0.0)/100))
    st.success(f"Calculated Saving: ₹ {saving:,.2f}")
    st.divider()
    
    daily_cache.append({
        "Date": date.today().strftime("%d/%m/%Y"), "Party Name": p_name, "Location": loc, "Vehicle No": v_no,
        "Revenue": auto_rev, "White Scrap (Qty)": (wq or 0.0), "Green Scrap (Qty)": (gq or 0.0),
        "Party Rate": (pr or 0.0), "Mill Rate": (mr or 0.0), "Report": (rep or 0.0), "Purchase": auto_pur,
        "Vehicle Charge": (ch or 0.0), "Total Saving": saving
    })

# BUTTONS
col_btn1, col_btn2, col_btn3 = st.columns(3)
if col_btn1.button("➕ Add Next Vehicle", use_container_width=True):
    st.session_state.rows_count += 1; st.rerun()

if col_btn2.button("❌ Remove Last Entry", use_container_width=True):
    if st.session_state.rows_count > 1:
        st.session_state.rows_count -= 1; st.rerun()

if col_btn3.button("🧹 Clear All", use_container_width=True):
    st.session_state.rows_count = 1; st.rerun()

st.divider()
tab1, tab2, tab3 = st.tabs(["🚀 Today's Sync", "📑 Range PDF Search", "📊 Master Database"])

with tab1:
    if st.button("🚀 SYNC & EMAIL TO SERVER", type="primary", use_container_width=True):
        df_today = pd.DataFrame(daily_cache)
        if os.path.exists(FULL_MASTER_PATH):
            df_today = pd.concat([pd.read_excel(FULL_MASTER_PATH), df_today], ignore_index=True)
        df_today.to_excel(FULL_MASTER_PATH, index=False)
        path = generate_report(pd.DataFrame(daily_cache), date.today().strftime("%d-%m-%Y"))
        ok, msg = send_to_server(path)
        if ok: st.success("Synced & Emailed!"); st.balloons()
        else: st.error(f"Email Failed: {msg}")

    if st.button("📄 Download Today's PDF", use_container_width=True):
        pdf_file = generate_report(pd.DataFrame(daily_cache), f"Today_{date.today()}")
        with open(pdf_file, "rb") as f: st.download_button("📥 Click to Download PDF", f, file_name=pdf_file, use_container_width=True)

with tab2:
    sd, ed = st.date_input("From", value=date.today()), st.date_input("To", value=date.today())
    if st.button("🔎 Generate Range Report", use_container_width=True):
        if os.path.exists(FULL_MASTER_PATH):
            mdf = pd.read_excel(FULL_MASTER_PATH)
            mdf['Parsed'] = pd.to_datetime(mdf['Date'], format='%d/%m/%Y').dt.date
            fdf = mdf[(mdf['Parsed'] >= sd) & (mdf['Parsed'] <= ed)].drop(columns=['Parsed'])
            if not fdf.empty:
                r_pdf = generate_report(fdf, f"Range_{sd}_to_{ed}")
                with open(r_pdf, "rb") as f: st.download_button("📥 Download Range PDF", f, file_name=r_pdf, use_container_width=True)

with tab3:
    if st.button("📊 Prepare Master Excel for Download", use_container_width=True):
        if os.path.exists(FULL_MASTER_PATH):
            with open(FULL_MASTER_PATH, "rb") as f: st.download_button("📥 Save Master.xlsx", f, file_name=MASTER_FILE, use_container_width=True)
