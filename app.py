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
    st.error("Add 'fpdf', 'openpyxl', and 'pandas' to your requirements.txt.")

# --- CREDENTIALS ---
USER_EMAIL = "saksham.xtm@gmail.com"
APP_PASSWORD = "up78ex2121" 

SAVE_FOLDER = "scrap_data_logs" 
MASTER_FILE = f"SCRAP_Master_{datetime.now().strftime('%m_%Y')}.xlsx"
FULL_MASTER_PATH = os.path.join(SAVE_FOLDER, MASTER_FILE)

if not os.path.exists(SAVE_FOLDER):
    os.makedirs(SAVE_FOLDER)

st.set_page_config(page_title="SCRAP MAIN SERVER", layout="wide", page_icon="🏢")

# --- PARTY NAME PRESETS ---
PARTY_LIST = ["Select Party", "Ganesh Steel", "RK Industries", "Modern Scrap", "City Traders", "Other (Type Below)"]

# --- PDF GENERATOR ---
class SCRAP_PDF(FPDF):
    def header(self):
        self.set_fill_color(220, 220, 220)
        self.set_font('Arial', 'B', 18)
        self.cell(0, 15, 'SCRAP (Main Server)', 1, 1, 'C', 1)
        self.set_font('Arial', 'I', 10)
        self.cell(0, 8, f'Official Ledger | {datetime.now().strftime("%d/%m/%Y")}', 0, 1, 'C')
        self.ln(5)

def generate_full_pdf(df, date_label):
    pdf = SCRAP_PDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 7)
    cols = {"Date": 22, "Vehicle": 28, "Party": 35, "Location": 25, "W.Qty": 18, "G.Qty": 18, "P.Rate": 18, "M.Rate": 18, "Report": 22, "Purch": 22, "Saving": 28}
    for title, width in cols.items():
        pdf.cell(width, 10, title, 1, 0, 'C', 1)
    pdf.ln()
    pdf.set_font("Arial", '', 7)
    total_sav = 0
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
        pdf.cell(cols["Report"], 10, f"{row['Report']:,.0f}", 1)
        pdf.cell(cols["Purch"], 10, f"{row['Purchase']:,.0f}", 1)
        s = float(row['Total Saving'])
        pdf.cell(cols["Saving"], 10, f"{s:,.2f}", 1)
        total_sav += s
        pdf.ln()
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 10, f"TOTAL NET SAVING: INR {total_sav:,.2f}", 0, 1, 'R')
    f_name = f"SCRAP_Full_Report_{date_label.replace('/','-')}.pdf"
    pdf.output(f_name)
    return f_name

def send_email_with_pdf(file_path):
    try:
        msg = MIMEMultipart()
        msg['From'] = USER_EMAIL
        msg['To'] = USER_EMAIL
        msg['Subject'] = f"SCRAP SERVER REPORT - {datetime.now().strftime('%d/%m/%Y')}"
        msg.attach(MIMEText("SCRAP (Main Server) Update attached.", 'plain'))
        with open(file_path, "rb") as a:
            p = MIMEBase('application', 'octet-stream')
            p.set_payload(a.read())
            encoders.encode_base64(p)
            p.add_header('Content-Disposition', f"attachment; filename= {os.path.basename(file_path)}")
            msg.attach(p)
        s = smtplib.SMTP('smtp.gmail.com', 587); s.starttls()
        s.login(USER_EMAIL, APP_PASSWORD); s.send_message(msg); s.quit()
        return True
    except Exception as e:
        st.error(f"Email Failed: {e}"); return False

# --- SESSION STATE FOR DYNAMIC ROWS ---
if 'vehicle_rows' not in st.session_state:
    st.session_state.vehicle_rows = [0] # Start with one row index

def add_vehicle():
    st.session_state.vehicle_rows.append(len(st.session_state.vehicle_rows))

# --- APP UI ---
st.title("🏗️ SCRAP (Main Server)")
st.write(f"Logged: **{USER_EMAIL}** | Date: **{date.today().strftime('%d/%m/%Y')}**")

curr_data = []

# Dynamic Entry Panel
with st.container():
    for i in st.session_state.vehicle_rows:
        with st.expander(f"🚛 Vehicle Entry #{i+1}", expanded=True):
            c1, c2, c3, c4 = st.columns(4)
            sel = c1.selectbox("Party", options=PARTY_LIST, key=f"sel_{i}")
            p_name = c1.text_input("New Party Name", key=f"pname_{i}") if sel in ["Select Party", "Other (Type Below)"] else sel
            loc = c2.text_input("Location", key=f"loc_{i}")
            v_no = c3.text_input("Vehicle No", key=f"vno_{i}")
            rev = c4.number_input("Total Revenue", value=None, key=f"rev_{i}")
            
            c5, c6, c7, c8 = st.columns(4)
            wq = c5.number_input("White Qty", value=None, key=f"wq_{i}")
            gq = c6.number_input("Green Qty", value=None, key=f"gq_{i}")
            pr = c7.number_input("Party Rate", value=None, key=f"pr_{i}")
            mr = c8.number_input("Mill Rate", value=None, key=f"mr_{i}")
            
            c9, c10, c11 = st.columns(3)
            rep = c9.number_input("Report", value=None, key=f"rep_{i}")
            pur = c10.number_input("Purchase", value=None, key=f"pur_{i}")
            ch = c11.number_input("Charge", value=None, key=f"ch_{i}")
            
            sav = ((pur or 0) - (rep or 0) - (ch or 0)) + ((rev or 0) * 0.36)
            
            curr_data.append({
                "Date": date.today().strftime("%d/%m/%Y"), "Party Name": p_name, 
                "Location": loc, "Vehicle No": v_no, "Revenue": (rev or 0), 
                "White Scrap (Qty)": (wq or 0), "Green Scrap (Qty)": (gq or 0), 
                "Party Rate": (pr or 0), "Mill Rate": (mr or 0), 
                "Report": (rep or 0), "Purchase": (pur or 0), 
                "Vehicle Charge": (ch or 0), "Total Saving": sav
            })

    if st.button("➕ Add Next Vehicle", use_container_width=True):
        add_vehicle()
        st.rerun()

# Action Buttons
st.divider()
b1, b2 = st.columns(2)
with b1:
    st.subheader("📊 Today's Actions")
    if st.button("🚀 SYNC & EMAIL TODAY'S DATA", use_container_width=True, type="primary"):
        df_today = pd.DataFrame(curr_data)
        if os.path.exists(FULL_MASTER_PATH):
            df_today = pd.concat([pd.read_excel(FULL_MASTER_PATH), df_today], ignore_index=True)
        df_today.to_excel(FULL_MASTER_PATH, index=False)
        pdf_path = generate_full_pdf(pd.DataFrame(curr_data), date.today().strftime("%d-%m-%Y"))
        if send_email_with_pdf(pdf_path):
            st.success("Synced to Server & Emailed!")
            st.balloons()
            
    if st.button("📄 Generate Today's PDF", use_container_width=True):
        today_pdf = generate_full_pdf(pd.DataFrame(curr_data), f"Today_{date.today().strftime('%d-%m-%Y')}")
        with open(today_pdf, "rb") as f:
            st.download_button("📥 Download Today's PDF", f, file_name=today_pdf, use_container_width=True)

with b2:
    st.subheader("🔍 Historical Tools")
    d1, d2 = st.date_input("Start", value=date.today()), st.date_input("End", value=date.today())
    sc1, sc2 = st.columns(2)
    if sc1.button("📑 Range PDF", use_container_width=True):
        if os.path.exists(FULL_MASTER_PATH):
            mdf = pd.read_excel(FULL_MASTER_PATH)
            mdf['P'] = pd.to_datetime(mdf['Date'], format='%d/%m/%Y').dt.date
            fdf = mdf[(mdf['P'] >= d1) & (mdf['P'] <= d2)].drop(columns=['P'])
            if not fdf.empty:
                rpdf = generate_full_pdf(fdf, f"{d1}_to_{d2}")
                with open(rpdf, "rb") as f: st.download_button("📥 Download Range PDF", f, file_name=rpdf)
    if sc2.button("📊 Master Excel", use_container_width=True):
        if os.path.exists(FULL_MASTER_PATH):
            with open(FULL_MASTER_PATH, "rb") as f: st.download_button("📥 Download Monthly Excel", f, file_name=MASTER_FILE)
