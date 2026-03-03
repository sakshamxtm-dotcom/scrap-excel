import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# --- SYSTEM STABILITY CHECK ---
try:
    from fpdf import FPDF
except ImportError:
    st.error("CRITICAL: fpdf library missing. Install it to enable PDF generation.")

# --- CONSTANTS & CREDENTIALS ---
USER_EMAIL = "saksham.xtm@gmail.com"
APP_PASSWORD = "up78ex2121" 
SAVE_FOLDER = "scrap_data_logs" 
MASTER_FILE = f"SCRAP_Master_{datetime.now().strftime('%m_%Y')}.xlsx"
FULL_MASTER_PATH = os.path.join(SAVE_FOLDER, MASTER_FILE)

if not os.path.exists(SAVE_FOLDER):
    os.makedirs(SAVE_FOLDER)

st.set_page_config(page_title="SCRAP MAIN SERVER", layout="wide", page_icon="🏢")

# --- DATA PRESETS ---
PARTY_LIST = ["Select Party", "Ganesh Steel", "RK Industries", "Modern Scrap", "City Traders", "Other (Type Below)"]

# --- PDF ENGINE (LANDSCAPE - ALL COLUMNS) ---
class SCRAP_PDF(FPDF):
    def header(self):
        self.set_fill_color(220, 220, 220)
        self.set_font('Arial', 'B', 18)
        self.cell(0, 15, 'SCRAP (Main Server)', 1, 1, 'C', 1)
        self.set_font('Arial', 'I', 10)
        self.cell(0, 8, f'Official Transaction Ledger | {datetime.now().strftime("%d/%m/%Y")}', 0, 1, 'C')
        self.ln(5)

def generate_full_report(df, label):
    pdf = SCRAP_PDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 7)
    
    # 11 Columns as requested
    cols = {
        "Date": 22, "Vehicle": 28, "Party": 35, "Location": 25, 
        "W.Qty": 18, "G.Qty": 18, "P.Rate": 18, "M.Rate": 18,
        "Report": 22, "Purch": 22, "Saving": 28
    }
    
    for title, width in cols.items():
        pdf.cell(width, 10, title, 1, 0, 'C', 1)
    pdf.ln()

    pdf.set_font("Arial", '', 7)
    total_sav = 0
    for _, row in df.iterrows():
        d_str = row['Date'] if isinstance(row['Date'], str) else row['Date'].strftime('%d/%m/%Y')
        pdf.cell(cols["Date"], 10, d_str, 1)
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
        total_sav += s_val
        pdf.ln()

    pdf.ln(5)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 10, f"TOTAL NET SAVING: INR {total_sav:,.2f}", 0, 1, 'R')
    
    fn = f"SCRAP_Report_{label.replace('/','-')}.pdf"
    pdf.output(fn)
    return fn

# --- MAIL ENGINE ---
def send_to_server(file_path):
    try:
        msg = MIMEMultipart()
        msg['From'], msg['To'] = USER_EMAIL, USER_EMAIL
        msg['Subject'] = f"SCRAP MAIN SERVER UPDATE: {datetime.now().strftime('%d/%m/%Y')}"
        msg.attach(MIMEText("SCRAP (Main Server) Official Sync Data.", 'plain'))
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
        st.error(f"Mail Server Error: {e}"); return False

# --- UI APP ---
st.title("🏗️ SCRAP (Main Server)")

if 'rows' not in st.session_state:
    st.session_state.rows = [0]

def add_row():
    st.session_state.rows.append(len(st.session_state.rows))

daily_cache = []

# --- DYNAMIC ENTRY LOOP ---
for i in st.session_state.rows:
    with st.expander(f"🚛 Vehicle Entry #{i+1}", expanded=True):
        # Line 1: Identification
        c1, c2, c3, c4 = st.columns(4)
        sel_p = c1.selectbox("Party", options=PARTY_LIST, key=f"sp_{i}")
        p_name = c1.text_input("Manual Party Name", key=f"mn_{i}") if sel_p in ["Select Party", "Other (Type Below)"] else sel_p
        loc, v_no = c2.text_input("Location", key=f"lc_{i}"), c3.text_input("Vehicle No", key=f"vn_{i}")
        rev = c4.number_input("Total Revenue", value=None, key=f"rv_{i}")
        
        # Line 2: Quantities & Rates
        c5, c6, c7, c8 = st.columns(4)
        wq, gq = c5.number_input("White Qty", value=None, key=f"wq_{i}"), c6.number_input("Green Qty", value=None, key=f"gq_{i}")
        pr, mr = c7.number_input("Party Rate", value=None, key=f"pr_{i}"), c8.number_input("Mill Rate", value=None, key=f"mr_{i}")
        
        # Line 3: Financials
        c9, c10, c11 = st.columns(3)
        rep, pur, ch = c9.number_input("Report", value=None, key=f"rp_{i}"), c10.number_input("Purchase", value=None, key=f"pu_{i}"), c11.number_input("Charge", value=None, key=f"ch_{i}")

        # Line 4: GST Input (Strict Order: Default 5% Purchase, 18% Sale)
        cg1, cg2 = st.columns(2)
        gst_p = cg1.number_input("GST Purchase %", value=5.0, key=f"gp_{i}")
        gst_s = cg2.number_input("GST Sale %", value=18.0, key=f"gs_{i}")

        # Calculation Logic
        r_val, p_val, rep_val, c_val = (rev or 0.0), (pur or 0.0), (rep or 0.0), (ch or 0.0)
        saving = (p_val - rep_val - c_val) + (r_val * (gst_p/100)) + (r_val * (gst_s/100))
        
        st.success(f"Calculated Saving: ₹ {saving:,.2f}")
        
        daily_cache.append({
            "Date": date.today().strftime("%d/%m/%Y"), "Party Name": p_name, "Location": loc, "Vehicle No": v_no,
            "Revenue": r_val, "White Scrap (Qty)": (wq or 0), "Green Scrap (Qty)": (gq or 0),
            "Party Rate": (pr or 0), "Mill Rate": (mr or 0), "Report": rep_val, "Purchase": p_val,
            "Vehicle Charge": c_val, "Total Saving": saving
        })

if st.button("➕ Add Next Vehicle", use_container_width=True):
    add_row(); st.rerun()

st.divider()

# --- THE THREE CORE TOOLS (Today, History, Excel) ---
t1, t2, t3 = st.columns(3)

with t1:
    st.subheader("📅 Today")
    if st.button("🚀 SYNC & EMAIL SERVER", type="primary", use_container_width=True):
        df_today = pd.DataFrame(daily_cache)
        if os.path.exists(FULL_MASTER_PATH):
            df_today = pd.concat([pd.read_excel(FULL_MASTER_PATH), df_today], ignore_index=True)
        df_today.to_excel(FULL_MASTER_PATH, index=False)
        path = generate_full_report(pd.DataFrame(daily_cache), date.today().strftime("%d-%m-%Y"))
        if send_to_server(path):
            st.toast("Sync Successful!", icon="✅")
            st.balloons()
    
    if st.button("📄 Today's PDF", use_container_width=True):
        pdf = generate_full_report(pd.DataFrame(daily_cache), f"Today_{date.today()}")
        with open(pdf, "rb") as f:
            st.download_button("📥 Download Today's PDF", f, file_name=pdf, use_container_width=True)

with t2:
    st.subheader("🔍 History (Range PDF)")
    sd = st.date_input("From", value=date.today(), key="sd")
    ed = st.date_input("To", value=date.today(), key="ed")
    if st.button("📑 Generate Range PDF", use_container_width=True):
        if os.path.exists(FULL_MASTER_PATH):
            mdf = pd.read_excel(FULL_MASTER_PATH)
            mdf['Parsed'] = pd.to_datetime(mdf['Date'], format='%d/%m/%Y').dt.date
            fdf = mdf[(mdf['Parsed'] >= sd) & (mdf['Parsed'] <= ed)].drop(columns=['Parsed'])
            if not fdf.empty:
                r_pdf = generate_full_report(fdf, f"Range_{sd}_to_{ed}")
                with open(r_pdf, "rb") as f:
                    st.download_button("📥 Download Range PDF", f, file_name=r_pdf, use_container_width=True)
            else: st.error("No data found for this range.")
        else: st.error("No Master Ledger found.")

with t3:
    st.subheader("📊 Database")
    if st.button("📥 Download Master Excel", use_container_width=True):
        if os.path.exists(FULL_MASTER_PATH):
            with open(FULL_MASTER_PATH, "rb") as f:
                st.download_button("📥 Save Master.xlsx", f, file_name=MASTER_FILE, use_container_width=True)
        else: st.error("File not created yet.")
