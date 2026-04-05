import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import dateutil.relativedelta as rd
import requests
from bs4 import BeautifulSoup

# --- 1. CME EXTRACTION LOGIC ---
@st.cache_data(ttl=3600)
def fetch_cme_sofr():
    """Attempts to visually extract the 3M Term SOFR from CME Group."""
    try:
        # Placeholder for the automated extraction logic from the CME URL
        return 3.67854 
    except:
        return 3.68000 

# --- 2. CORE UTILITIES ---
def get_next_dates(ref_ex_str, pay_day_target):
    today = datetime.now()
    current_ex = datetime.strptime(ref_ex_str, '%m/%d/%Y')
    while current_ex <= today:
        current_ex += rd.relativedelta(months=3)
    next_pay = current_ex.replace(day=pay_day_target)
    if next_pay < current_ex:
        next_pay += rd.relativedelta(months=1)
    return current_ex.date(), next_pay.date()

def get_30_360_days(start, end):
    d1 = min(start.day, 30)
    d2 = 30 if (d1 >= 30 and end.day == 31) else end.day
    if start.month == 2 and (start + timedelta(days=1)).month == 3: d1 = 30
    if end.month == 2 and (end + timedelta(days=1)).month == 3: d2 = 30
    return (end.year - start.year) * 360 + (end.month - start.month) * 30 + (d2 - d1)

# --- 3. THE COMPLETE DATASET (24 TICKERS) ---
SOFR_DATA = {
    'AGNCM': {'spread': 0.0516 + 0.0026161, 'yahoo': 'AGNCM',  'ref_ex': '03/31/2024', 'pay_day': 15},
    'AGNCN': {'spread': 0.0463 + 0.0026161, 'yahoo': 'AGNCN',  'ref_ex': '03/31/2024', 'pay_day': 15},
    'AGNCO': {'spread': 0.0496 + 0.0026161, 'yahoo': 'AGNCO',  'ref_ex': '03/31/2024', 'pay_day': 15},
    'AGNCP': {'spread': 0.0510 + 0.0026161, 'yahoo': 'AGNCP',  'ref_ex': '03/31/2024', 'pay_day': 15},
    'NLY-F': {'spread': 0.0499 + 0.0026161, 'yahoo': 'NLY-PF', 'ref_ex': '03/01/2024', 'pay_day': 15},
    'NLY-G': {'spread': 0.0417 + 0.0026161, 'yahoo': 'NLY-PG', 'ref_ex': '02/28/2024', 'pay_day': 15},
    'NLY-I': {'spread': 0.0499 + 0.0026161, 'yahoo': 'NLY-PI', 'ref_ex': '03/01/2024', 'pay_day': 15},
    'DX-C':  {'spread': 0.0546 + 0.0026161, 'yahoo': 'DX-PC',  'ref_ex': '03/28/2024', 'pay_day': 15},
    'RITM-A':{'spread': 0.0580 + 0.0026161, 'yahoo': 'RITM-PA', 'ref_ex': '02/28/2024', 'pay_day': 15},
    'RITM-B':{'spread': 0.0564 + 0.0026161, 'yahoo': 'RITM-PB', 'ref_ex': '02/28/2024', 'pay_day': 15},
    'RITM-C':{'spread': 0.0491 + 0.0026161, 'yahoo': 'RITM-PC', 'ref_ex': '02/28/2024', 'pay_day': 15},
    'PMT-A': {'spread': 0.0583 + 0.0026161, 'yahoo': 'PMT-PA',  'ref_ex': '02/28/2024', 'pay_day': 15},
    'PMT-B': {'spread': 0.0566 + 0.0026161, 'yahoo': 'PMT-PB',  'ref_ex': '02/28/2024', 'pay_day': 15},
    'MFA-C': {'spread': 0.0534 + 0.0026161, 'yahoo': 'MFA-PC',  'ref_ex': '03/28/2024', 'pay_day': 15},
    'CIM-B': {'spread': 0.0580 + 0.0026161, 'yahoo': 'CIM-PB',  'ref_ex': '02/28/2024', 'pay_day': 15},
    'CIM-C': {'spread': 0.0507 + 0.0026161, 'yahoo': 'CIM-PC',  'ref_ex': '02/28/2024', 'pay_day': 15},
    'CIM-D': {'spread': 0.0497 + 0.0026161, 'yahoo': 'CIM-PD',  'ref_ex': '02/28/2024', 'pay_day': 15},
    'IVR-C': {'spread': 0.0528 + 0.0026161, 'yahoo': 'IVR-PC',  'ref_ex': '03/14/2024', 'pay_day': 15},
    'CHMI-B':{'spread': 0.0599 + 0.0026161, 'yahoo': 'CHMI-PB', 'ref_ex': '03/14/2024', 'pay_day': 15},
    'MITT-C':{'spread': 0.0648 + 0.0026161, 'yahoo': 'MITT-PC', 'ref_ex': '03/14/2024', 'pay_day': 15},
    'GPMT-A':{'spread': 0.0583 + 0.0026161, 'yahoo': 'GPMT-PA', 'ref_ex': '03/14/2024', 'pay_day': 15},
    'ADAMM': {'spread': 0.0647,             'yahoo': 'ADAMM',  'ref_ex': '03/15/2024', 'pay_day': 15},
    'ADAML': {'spread': 0.0613,             'yahoo': 'ADAML',  'ref_ex': '03/15/2024', 'pay_day': 15},
    'ADAMN': {'spread': 0.0592,             'yahoo': 'ADAMN',  'ref_ex': '03/15/2024', 'pay_day': 15}
}

# --- 4. UI SETUP ---
st.set_page_config(page_title="3M Term SOFR Tracker", layout="wide")
st.title("📈 3-Month Term SOFR Preferreds")

cme_val = fetch_cme_sofr()

row1_col1, row1_col2, row1_col3, _ = st.columns([1.5, 1.5, 1.5, 3])

with row1_col1:
    fwd_sofr = st.number_input("Current 3M Term SOFR (%)", value=cme_val, step=0.00001, format="%.5f")
with row1_col2:
    hist_sofr = st.number_input("Last Reset Term SOFR (%)", value=fwd_sofr, step=0.00001, format="%.5f")
with row1_col3:
    increment_bps = st.number_input("Increment (BPS)", value=50, step=10)

st.markdown(
    f"<p style='font-size: 0.78rem; color: #808495; margin-top: -18px; margin-bottom: 20px;'>"
    f"Note: Rates may not reflect real-time CME fixings. Please verify and update Current and Last Reset values manually for precise results."
    f"</p>", 
    unsafe_allow_html=True
)

# --- 5. DATA PROCESSING ---
today = datetime.now()
main_rows = []
sens_rows = []
inc_dec = increment_bps / 10000  
target_rates = [(fwd_sofr/100) + (i * inc_dec) for i in range(-2, 3)]

for ticker, info in SOFR_DATA.items():
    try:
        price = float(yf.Ticker(info['yahoo']).history(period="1d")['Close'].iloc[-1])
    except: price = 25.0
    
    next_ex, next_pay = get_next_dates(info['ref_ex'], info['pay_day'])
    prior_ex = next_ex - rd.relativedelta(months=3)
    
    # Accrual (Last Reset Rate)
    curr_coupon_rate = (hist_sofr / 100) + info['spread']
    days_accrued = get_30_360_days(prior_ex, today.date())
    accrued = (25 * curr_coupon_rate) * (days_accrued / 360)
    
    # Forward (Current Rate)
    fwd_coupon_rate = (fwd_sofr / 100) + info['spread']
    clean_p = price - accrued
    yld = (fwd_coupon_rate * 25) / clean_p if clean_p > 0 else 0

    main_rows.append({
        "Ticker": ticker,
        "Coupon (Locked)": curr_coupon_rate * 100,
        "Price": price,
        "Accrued": accrued,
        "Full Qtr Div": (25 * curr_coupon_rate) / 4,
        "Clean Price": clean_p,
        "Curr Yield": yld * 100,
        "Spread (+CAS)": info['spread'] * 100,
        "Next Ex-Div": next_ex,
        "Next Pay": next_pay
    })

    # Sensitivity Logic
    s_row = {"Ticker": ticker}
    for r in target_rates:
        label = f"{r*100:.2f}% SOFR"
        s_yld = ((r + info['spread']) * 25) / clean_p if clean_p > 0 else 0
        s_row[label] = s_yld * 100
    sens_rows.append(s_row)

# --- 6. RENDER DASHBOARD ---
st.subheader("Portfolio Performance")
st.dataframe(pd.DataFrame(main_rows), use_container_width=True, hide_index=True)

st.divider()

st.subheader(f"Yield Sensitivity (Forward @ {fwd_sofr:.5f}% SOFR)")
df_sens = pd.DataFrame(sens_rows)
sens_config = {col: st.column_config.NumberColumn(format="%.2f%%") for col in df_sens.columns if col != "Ticker"}
st.dataframe(df_sens, use_container_width=True, hide_index=True, column_config=sens_config)
