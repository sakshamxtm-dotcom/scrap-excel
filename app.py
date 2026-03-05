import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
from fpdf import FPDF

# --- SETTINGS ---
SAVE_FOLDER = "scrap_data_logs"
MASTER_FILE = f"SCRAP_Master_{datetime.now().strftime('%m_%Y')}.xlsx"
FULL_PATH = os.path.join(SAVE_FOLDER, MASTER_FILE)

if not os.path.exists(SAVE_FOLDER):
    os.makedirs(SAVE_FOLDER)

st.set_page_config(page_title="SCRAP SERVER", layout="wide")

# --- PDF ENGINE ---
class SCRAP_PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'SCRAP OFFICIAL LEDGER', 0, 1, 'C')
        self.ln(5)

def create_pdf(df, filename):
    pdf = SCRAP_PDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 8)
    pdf.set_fill_color(200, 200, 200)
    cols = ["Date", "Party Name", "Vehicle No", "Total Revenue", "Net Purchase", "Total Saving"]
    for col in cols: pdf.cell(45, 10, col, 1, 0, 'C', 1)
    pdf.ln()
    pdf.set_font("Arial", '', 8)
    for _, row in df.iterrows():
        for col in cols: pdf.cell(45, 10, str(row[col]), 1)
        pdf.ln()
    pdf.output(filename)
    return filename

# --- UI LOGIC ---
st.title("🏗️ SCRAP Main Ledger")

if 'rows' not in st.session_state:
    st.session_state.rows = 1

current_entries = []

# --- INPUT SECTION ---
for i in range(st.session_state.rows):
    with st.expander(f"🚛 Vehicle Entry #{i+1}", expanded=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        p_name = c1.text_input("Party Name", key=f"p_{i}")
        v_no = c2.text_input("Vehicle No", key=f"v_{i}")
        loc = c3.text_input("Location", key=f"l_{i}")

        f1, f2, f3, f4, f5, f6, f7 = st.columns(7)
        wq = f1.number_input("White Qty(H)", value=None, key=f"wq_{i}")
        gq = f2.number_input("Green Qty(G)", value=None, key=f"gq_{i}")
        pr = f3.number_input("Party Rate(I)", value=None, key=f"pr_{i}")
        mr = f4.number_input("Mill Rate(J)", value=None, key=f"mr_{i}")
        rep = f5.number_input("Report(K)", value=None, key=f"rp_{i}")
        ch = f6.number_input("Charge(F)", value=None, key=f"ch_{i}")
        pgst = f7.number_input("Purc. GST (Manual)", value=None, key=f"pgst_{i}")
        
        # --- CALCULATION ENGINE ---
        t_qty = (wq or 0) + (gq or 0)
        base_rev = (pr or 0) * t_qty
        sale_gst_val = base_rev * 0.18
        final_rev = base_rev + sale_gst_val
        
        raw_pur = ((mr or 0) - (pr or 0)) * t_qty
        net_pur = raw_pur - (rep or 0) - (ch or 0) - (pgst or 0)
        tsaving = net_pur + sale_gst_val

        current_entries.append({
            "Date": date.today().strftime("%d/%m/%Y"),
            "Party Name": p_name or "---", "Vehicle No": v_no or "---", "Location": loc,
            "White Scrap": wq or 0, "Green Scrap": gq or 0,
            "Total Revenue": round(final_rev, 2),
            "Sale GST (18%)": round(sale_gst_val, 2),
            "Net Purchase": round(net_pur, 2),
            "Total Saving": round(tsaving, 2),
            "Manual Purc GST": pgst or 0, "Report": rep or 0, "Charge": ch or 0
        })

# --- LIVE PREVIEW TABLE ---
st.subheader("📋 Live Preview (Calculated Data)")
preview_df = pd.DataFrame(current_entries)
st.dataframe(preview_df[["Party Name", "Vehicle No", "Total Revenue", "Sale GST (18%)", "Net Purchase", "Total Saving"]], use_container_width=True)

# --- ROW MANAGEMENT ---
btn_c1, btn_c2, btn_c3 = st.columns(3)
if btn_c1.button("➕ Add Vehicle", use_container_width=True):
    st.session_state.rows += 1; st.rerun()
if btn_c2.button("❌ Remove Last", use_container_width=True) and st.session_state.rows > 1:
    st.session_state.rows -= 1; st.rerun()
if btn_c3.button("🧹 Clear All", use_container_width=True):
    st.session_state.rows = 1; st.rerun()

# --- EXPORT SECTION ---
st.divider()
if st.button("🚀 SYNC TO MASTER & GENERATE PDF", type="primary", use_container_width=True):
    try:
        # Update Excel
        if os.path.exists(FULL_PATH):
            master_df = pd.read_excel(FULL_PATH)
            final_df = pd.concat([master_df, preview_df], ignore_index=True)
        else:
            final_df = preview_df
        final_df.to_excel(FULL_PATH, index=False)
        
        # Create PDF
        pdf_name = f"Report_{date.today()}.pdf"
        create_pdf(preview_df, pdf_name)
        
        st.success("✅ Data Synced Successfully!")
        dl_c1, dl_c2 = st.columns(2)
        with open(pdf_name, "rb") as f:
            dl_c1.download_button("📥 Download PDF Report", f, file_name=pdf_name, use_container_width=True)
        with open(FULL_PATH, "rb") as f:
            dl_c2.download_button("📥 Download Master Excel", f, file_name=MASTER_FILE, use_container_width=True)
            
    except Exception as e:
        st.error(f"Error: {e}")
