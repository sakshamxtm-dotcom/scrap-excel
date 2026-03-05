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

# --- PDF CLASS ---
class SCRAP_PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'SCRAP OFFICIAL LEDGER', 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, f'Generated on: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 1, 'C')
        self.ln(5)

def create_pdf(df, filename):
    pdf = SCRAP_PDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 8)
    pdf.set_fill_color(220, 220, 220)
    
    # Column Widths
    cols = {"Date": 22, "Party": 35, "Vehicle": 25, "W.Qty": 15, "G.Qty": 15, "Rev(+18%)": 25, "Net Purch": 25, "Saving": 25}
    
    for title, width in cols.items():
        pdf.cell(width, 10, title, 1, 0, 'C', 1)
    pdf.ln()
    
    pdf.set_font("Arial", '', 8)
    for _, row in df.iterrows():
        pdf.cell(22, 10, str(row['Date']), 1)
        pdf.cell(35, 10, str(row['Party Name'])[:20], 1)
        pdf.cell(25, 10, str(row['Vehicle No']), 1)
        pdf.cell(15, 10, str(row['White Scrap']), 1)
        pdf.cell(15, 10, str(row['Green Scrap']), 1)
        pdf.cell(25, 10, f"{row['Total Revenue']:,.0f}", 1)
        pdf.cell(25, 10, f"{row['Net Purchase']:,.0f}", 1)
        pdf.cell(25, 10, f"{row['Total Saving']:,.0f}", 1)
        pdf.ln()
    
    pdf.output(filename)
    return filename

# --- UI LOGIC ---
st.title("🏗️ SCRAP Main Ledger")

if 'rows' not in st.session_state:
    st.session_state.rows = 1

entries = []
for i in range(st.session_state.rows):
    with st.container():
        st.subheader(f"🚛 Vehicle Entry #{i+1}")
        col1, col2, col3 = st.columns([2, 1, 1])
        p_name = col1.text_input(f"Party Name", key=f"p_{i}")
        v_no = col2.text_input(f"Vehicle No", key=f"v_{i}")
        loc = col3.text_input(f"Location", key=f"l_{i}")

        f1, f2, f3, f4, f5, f6, f7 = st.columns(7)
        wq = f1.number_input("White Qty(H)", value=None, key=f"wq_{i}")
        gq = f2.number_input("Green Qty(G)", value=None, key=f"gq_{i}")
        pr = f3.number_input("Party Rate(I)", value=None, key=f"pr_{i}")
        mr = f4.number_input("Mill Rate(J)", value=None, key=f"mr_{i}")
        rep = f5.number_input("Report(K)", value=None, key=f"rp_{i}")
        ch = f6.number_input("Charge(F)", value=None, key=f"ch_{i}")
        pgst = f7.number_input("Purc. GST (Manual)", value=None, key=f"pgst_{i}")
        
        # Calculations
        t_qty = (wq or 0) + (gq or 0)
        base_rev = (pr or 0) * t_qty
        sale_gst_val = base_rev * 0.18
        final_rev = base_rev + sale_gst_val
        
        raw_pur = ((mr or 0) - (pr or 0)) * t_qty
        net_pur = raw_pur - (rep or 0) - (ch or 0) - (pgst or 0)
        # Saving = Final Revenue - (Report + Charge + Manual GST + Party Cost) 
        # Or more simply based on your previous logic:
        tsaving = net_pur + sale_gst_val

        entries.append({
            "Date": date.today().strftime("%d/%m/%Y"),
            "Party Name": p_name, "Vehicle No": v_no, "Location": loc,
            "Vehicle Charge": (ch or 0), "Green Scrap": (gq or 0), "White Scrap": (wq or 0),
            "Party Rate": (pr or 0), "Mill Rate": (mr or 0), "Report Amount": (rep or 0),
            "Manual Purchase GST": (pgst or 0), "Sale GST (18%)": sale_gst_val,
            "Total Revenue": final_rev, "Net Purchase": net_pur, "Total Saving": tsaving
        })
        st.divider()

# --- ROW MANAGEMENT ---
c1, c2, c3 = st.columns(3)
if c1.button("➕ Add Vehicle"):
    st.session_state.rows += 1; st.rerun()
if c2.button("❌ Remove Last") and st.session_state.rows > 1:
    st.session_state.rows -= 1; st.rerun()
if c3.button("🧹 Clear All"):
    st.session_state.rows = 1; st.rerun()

# --- PROCESSING ---
st.divider()
tab1, tab2 = st.tabs(["🚀 Sync & Export", "📑 Master History"])

with tab1:
    if st.button("🚀 PROCESS & GENERATE PDF/EXCEL", type="primary", use_container_width=True):
        df_current = pd.DataFrame(entries)
        
        # Save to Master Excel
        try:
            if os.path.exists(FULL_PATH):
                master_df = pd.read_excel(FULL_PATH)
                final_df = pd.concat([master_df, df_current], ignore_index=True)
            else:
                final_df = df_current
            final_df.to_excel(FULL_PATH, index=False)
            st.success("Master File Updated!")
            
            # Generate PDF
            pdf_name = f"SCRAP_Report_{date.today()}.pdf"
            create_pdf(df_current, pdf_name)
            
            col_dl1, col_dl2 = st.columns(2)
            with open(pdf_name, "rb") as f:
                col_dl1.download_button("📥 Download PDF Report", f, file_name=pdf_name, use_container_width=True)
            with open(FULL_PATH, "rb") as f:
                col_dl2.download_button("📥 Download Full Master (.xlsx)", f, file_name=MASTER_FILE, use_container_width=True)
                
        except Exception as e:
            st.error(f"Error: {e}")

with tab2:
    if os.path.exists(FULL_PATH):
        st.dataframe(pd.read_excel(FULL_PATH))
    else:
        st.info("No master data found yet.")
