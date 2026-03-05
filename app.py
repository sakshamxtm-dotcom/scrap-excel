import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

# --- SETTINGS ---
SAVE_FOLDER = "scrap_data_logs"
MASTER_FILE = f"SCRAP_Master_{datetime.now().strftime('%m_%Y')}.xlsx"
FULL_PATH = os.path.join(SAVE_FOLDER, MASTER_FILE)

if not os.path.exists(SAVE_FOLDER):
    os.makedirs(SAVE_FOLDER)

st.set_page_config(page_title="SCRAP SERVER", layout="wide")
st.title("🏗️ SCRAP Main Ledger")

if 'rows' not in st.session_state:
    st.session_state.rows = 1

entries = []
for i in range(st.session_state.rows):
    with st.container():
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
        
        # Immediate calculation for display
        t_qty = (wq or 0) + (gq or 0)
        base_rev = (pr or 0) * t_qty
        sale_gst_val = base_rev * 0.18
        final_rev = base_rev + sale_gst_val
        
        raw_pur = ((mr or 0) - (pr or 0)) * t_qty
        net_pur = raw_pur - (rep or 0) - (ch or 0) - (pgst or 0)
        
        # Displaying the calculated Sale GST & Net Purchase for user clarity
        d1, d2, d3 = st.columns(3)
        d1.metric("Sale GST (18%)", f"₹ {sale_gst_val:,.2f}")
        d2.metric("Total Revenue (+GST)", f"₹ {final_rev:,.2f}")
        d3.metric("Net Purchase", f"₹ {net_pur:,.2f}")

        entries.append({
            "Date": date.today().strftime("%d/%m/%Y"),
            "Party Name": p_name, "Vehicle No": v_no, "Location": loc,
            "Vehicle Charge": ch, "Green Scrap": gq, "White Scrap": wq,
            "Party Rate": pr, "Mill Rate": mr, "Report Amount": rep,
            "Manual Purchase GST": pgst, "Sale GST (18%)": sale_gst_val,
            "Total Revenue": final_rev, "Net Purchase": net_pur
        })
        st.divider()

# --- ROW MANAGEMENT ---
c1, c2, c3 = st.columns(3)
if c1.button("➕ Add Vehicle", use_container_width=True):
    st.session_state.rows += 1; st.rerun()
if c2.button("❌ Remove Last", use_container_width=True) and st.session_state.rows > 1:
    st.session_state.rows -= 1; st.rerun()
if c3.button("🧹 Clear All", use_container_width=True):
    st.session_state.rows = 1; st.rerun()

# --- PROCESSING ---
if st.button("🚀 PROCESS & SAVE TO MASTER", type="primary", use_container_width=True):
    df = pd.DataFrame(entries).fillna(0)
    
    # Vectorized Saving Calculation (Final Step)
    df['Total Saving'] = df['Net Purchase'] + (df['Total Revenue'] * 0.18) # Adjust this if savings logic changes further
    
    try:
        if os.path.exists(FULL_PATH):
            master_df = pd.read_excel(FULL_PATH)
            df = pd.concat([master_df, df], ignore_index=True)
        
        df.to_excel(FULL_PATH, index=False)
        st.success(f"Calculated and Saved {len(entries)} entries!")
        st.dataframe(df.tail(len(entries)))
    except Exception as e:
        st.error(f"Error: {e}")

if os.path.exists(FULL_PATH):
    with open(FULL_PATH, "rb") as f:
        st.download_button("📥 Download Master Excel", f, file_name=MASTER_FILE)
     
