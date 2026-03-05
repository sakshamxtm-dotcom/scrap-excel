import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from fpdf import FPDF

# --- SYSTEM CONSTANTS ---
USER_EMAIL = "saksham.xtm@gmail.com"
APP_PASSWORD = "iqpz gprg zbnv kfam" 
SAVE_FOLDER = "scrap_data_logs" 
MASTER_FILE = f"SCRAP_Master_{datetime.now().strftime('%m_%Y')}.xlsx"
FULL_PATH = os.path.join(SAVE_FOLDER, MASTER_FILE)

if not os.path.exists(SAVE_FOLDER):
    os.makedirs(SAVE_FOLDER)

st.set_page_config(page_title="SCRAP SERVER", layout="wide")

# --- PDF ENGINE ---
class SCRAP_PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'SCRAP OFFICIAL LEDGER REPORT', 0, 1, 'C')
        self.set_font('Arial', 'I', 9)
        self.cell(0, 10, f'Generated: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 1, 'C')
        self.ln(5)

def create_pdf(df, filename):
    pdf = SCRAP_PDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 8)
    pdf.set_fill_color(230, 230, 230)
    cols = ["Date", "Party Name", "Vehicle No", "Sale GST", "Total Revenue", "Total Purchase", "Total Saving"]
    widths = [25, 50, 35, 35, 45, 45, 40]
    
    for i, col in enumerate(cols):
        pdf.cell(widths[i], 10, col, 1, 0, 'C', 1)
    pdf.ln()
    
    pdf.set_font("Arial", '', 8)
    for _, row in df.iterrows():
        for i, col in enumerate(cols):
            pdf.cell(widths[i], 10, str(row[col]), 1)
        pdf.ln()
    pdf.output(filename)
    return filename

# --- EMAIL ENGINE ---
def email_report(file_path):
    try:
        msg = MIMEMultipart()
        msg['From'], msg['To'] = USER_EMAIL, USER_EMAIL
        msg['Subject'] = f"SCRAP Backup: {datetime.now().strftime('%d/%m/%Y')}"
        msg.attach(MIMEText("Automated SCRAP Ledger Backup.", 'plain'))
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
st.title("🏗️ SCRAP Main Ledger & Server")

if 'rows' not in st.session_state: st.session_state.rows = 1

current_entries = []
for i in range(st.session_state.rows):
    with st.expander(f"🚛 Vehicle Entry #{i+1}", expanded=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        p_name, v_no, loc = c1.text_input("Party", key=f"p_{i}"), c2.text_input("Vehicle", key=f"v_{i}"), c3.text_input("Location", key=f"l_{i}")

        f1, f2, f3, f4, f5, f6, f7 = st.columns(7)
        wq, gq = f1.number_input("White Qty", value=None, key=f"wq_{i}"), f2.number_input("Green Qty", value=None, key=f"gq_{i}")
        pr, mr = f3.number_input("Party Rate", value=None, key=f"pr_{i}"), f4.number_input("Mill Rate", value=None, key=f"mr_{i}")
        rep, ch, pgst = f5.number_input("Report", value=None, key=f"rp_{i}"), f6.number_input("Charge", value=None, key=f"ch_{i}"), f7.number_input("Manual Purc GST", value=None, key=f"pgst_{i}")
        
        # Calculation Engine
        t_qty = (wq or 0.0) + (gq or 0.0)
        base_rev = (pr or 0.0) * t_qty
        sale_gst_val = base_rev * 0.18
        final_rev = base_rev + sale_gst_val
        net_pur = (((mr or 0.0) - (pr or 0.0)) * t_qty) - (rep or 0.0) - (ch or 0.0) - (pgst or 0.0)
        tsaving = net_pur + sale_gst_val

        m1, m2, m3 = st.columns(3)
        m1.metric("Sale GST", f"₹ {sale_gst_val:,.2f}"); m2.metric("Total Revenue", f"₹ {final_rev:,.2f}"); m3.metric("Total Purchase", f"₹ {net_pur:,.2f}")

        current_entries.append({
            "Date": date.today().strftime("%d/%m/%Y"), "Party Name": p_name or "---", "Vehicle No": v_no or "---",
            "Sale GST": round(sale_gst_val, 2), "Total Revenue": round(final_rev, 2), "Total Purchase": round(net_pur, 2), "Total Saving": round(tsaving, 2)
        })

# --- CONTROLS ---
btn_c1, btn_c2, btn_c3 = st.columns(3)
if btn_c1.button("➕ Add Vehicle", use_container_width=True): st.session_state.rows += 1; st.rerun()
if btn_c2.button("❌ Remove Last", use_container_width=True) and st.session_state.rows > 1: st.session_state.rows -= 1; st.rerun()
if btn_c3.button("🧹 Clear All", use_container_width=True): st.session_state.rows = 1; st.rerun()

# --- TABS FOR EXPORT ---
st.divider()
tab1, tab2, tab3 = st.tabs(["🚀 Sync & Email", "📑 Range PDF Search", "📊 Master Database"])

with tab1:
    if st.button("🚀 SYNC, SAVE & EMAIL BACKUP", type="primary", use_container_width=True):
        df_today = pd.DataFrame(current_entries)
        if os.path.exists(FULL_PATH):
            df_today = pd.concat([pd.read_excel(FULL_PATH), df_today], ignore_index=True)
        df_today.to_excel(FULL_PATH, index=False)
        
        pdf_name = f"Daily_Report_{date.today()}.pdf"
        create_pdf(pd.DataFrame(current_entries), pdf_name)
        
        ok, msg = email_report(pdf_name)
        if ok: st.success("Synced & Emailed!"); st.balloons()
        else: st.error(f"Email Failed: {msg}")
        
        with open(pdf_name, "rb") as f: st.download_button("📥 Download Today's PDF", f, file_name=pdf_name)

with tab2:
    d_col1, d_col2 = st.columns(2)
    start_d = d_col1.date_input("From Date", value=date.today())
    end_d = d_col2.date_input("To Date", value=date.today())
    if st.button("🔎 Generate Range PDF", use_container_width=True):
        if os.path.exists(FULL_PATH):
            mdf = pd.read_excel(FULL_PATH)
            mdf['Parsed'] = pd.to_datetime(mdf['Date'], format='%d/%m/%Y').dt.date
            fdf = mdf[(mdf['Parsed'] >= start_d) & (mdf['Parsed'] <= end_d)].drop(columns=['Parsed'])
            if not fdf.empty:
                range_pdf = f"Range_{start_d}_to_{end_d}.pdf"
                create_pdf(fdf, range_pdf)
                with open(range_pdf, "rb") as f: st.download_button("📥 Download Range PDF", f, file_name=range_pdf)
            else: st.warning("No data found for this range.")

with tab3:
    if os.path.exists(FULL_PATH):
        st.dataframe(pd.read_excel(FULL_PATH), use_container_width=True)
        with open(FULL_PATH, "rb") as f: st.download_button("📥 Download Master Excel", f, file_name=MASTER_FILE)
    else: st.info("Master Ledger is empty.")
