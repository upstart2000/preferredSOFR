import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import dateutil.relativedelta as rd

# --- 1. CORE UTILITIES ---
def get_next_dates(ref_ex_str, ref_pay_str):
    today = datetime.now()
    curr_ex = datetime.strptime(ref_ex_str, '%m/%d/%Y')
    curr_pay = datetime.strptime(ref_pay_str, '%m/%d/%Y')
    while curr_ex <= today:
        curr_ex += rd.relativedelta(months=3)
        curr_pay += rd.relativedelta(months=3)
    return curr_ex.date(), curr_pay.date()

def get_30_360_days(start, end):
    d1 = min(start.day, 30)
    d2 = 30 if (d1 >= 30 and end.day == 31) else end.day
    if start.month == 2 and (start + timedelta(days=1)).month == 3: d1 = 30
    if end.month == 2 and (end + timedelta(days=1)).month == 3: d2 = 30
    return (end.year - start.year) * 360 + (end.month - start.month) * 30 + (d2 - d1)

# --- 2. AUDITED DATASET (Synced to Spreadsheet Col Q & M) ---
CAS = 0.00261

SOFR_DATA = {
    # AGNC: Ex-Div is 1st of Jan/Apr/Jul/Oct. Pay is 15th.
    'AGNCM': {'spread': 0.0516 + CAS, 'yahoo': 'AGNCM',  'ref_ex': '04/01/2024', 'ref_pay': '04/15/2024'},
    'AGNCN': {'spread': 0.0463 + CAS, 'yahoo': 'AGNCN',  'ref_ex': '04/01/2024', 'ref_pay': '04/15/2024'},
    'AGNCO': {'spread': 0.0496 + CAS, 'yahoo': 'AGNCO',  'ref_ex': '04/01/2024', 'ref_pay': '04/15/2024'},
    'AGNCP': {'spread': 0.0510 + CAS, 'yahoo': 'AGNCP',  'ref_ex': '04/01/2024', 'ref_pay': '04/15/2024'},
    # NLY: Ex-Div is 1st. Pay is Month-End.
    'NLY-F': {'spread': 0.0499 + CAS, 'yahoo': 'NLY-PF', 'ref_ex': '03/01/2024', 'ref_pay': '03/31/2024'},
    'NLY-G': {'spread': 0.0417 + CAS, 'yahoo': 'NLY-PG', 'ref_ex': '03/01/2024', 'ref_pay': '03/31/2024'},
    'NLY-I': {'spread': 0.0499 + CAS, 'yahoo': 'NLY-PI', 'ref_ex': '03/01/2024', 'ref_pay': '03/31/2024'},
    # DX-C: Ex-Div is 1st. Pay is 15th.
    'DX-C':  {'spread': 0.0546 + CAS, 'yahoo': 'DX-PC',  'ref_ex': '04/01/2024', 'ref_pay': '04/15/2024'},
    # RITM: Ex-Div is 1st. Pay is 15th.
    'RITM-A':{'spread': 0.0580 + CAS, 'yahoo': 'RITM-PA', 'ref_ex': '02/01/2024', 'ref_pay': '02/15/2024'},
    'RITM-B':{'spread': 0.0564 + CAS, 'yahoo': 'RITM-PB', 'ref_ex': '02/01/2024', 'ref_pay': '02/15/2024'},
    'RITM-C':{'spread': 0.0491 + CAS, 'yahoo': 'RITM-PC', 'ref_ex': '02/01/2024', 'ref_pay': '02/15/2024'},
    # MFA-C: Ex-Div is 3rd. Pay is Month-End.
    'MFA-C': {'spread': 0.0534 + CAS, 'yahoo': 'MFA-PC',  'ref_ex': '03/03/2024', 'ref_pay': '03/31/2024'},
    # CIM: Ex-Div is 1st. Pay is 30th (per Col M "2024-03-30").
    'CIM-B': {'spread': 0.0580 + CAS, 'yahoo': 'CIM-PB',  'ref_ex': '03/01/2024', 'ref_pay': '03/30/2024'},
    'CIM-C': {'spread': 0.0507 + CAS, 'yahoo': 'CIM-PC',  'ref_ex': '03/01/2024', 'ref_pay': '03/30/2024'},
    'CIM-D': {'spread': 0.0497 + CAS, 'yahoo': 'CIM-PD',  'ref_ex': '03/01/2024', 'ref_pay': '03/30/2024'},
    # CHMI-B: Ex-Div is 1st. Pay is 15th.
    'CHMI-B':{'spread': 0.0599 + CAS, 'yahoo': 'CHMI-PB', 'ref_ex': '04/01/2024', 'ref_pay': '04/15/2024'},
    # MITT-C: Ex-Div is Month-End (Spreadsheet says 2026-05-29).
    'MITT-C':{'spread': 0.0648 + CAS, 'yahoo': 'MITT-PC', 'ref_ex': '02/28/2024', 'ref_pay': '03/17/2024'},
    # ADAM: ADAMM uses Spread 6.429% + CAS. ADAML is SOFR-native.
    'ADAMM': {'spread': 0.06429+ CAS, 'yahoo': 'ADAMM',  'ref_ex': '04/01/2024', 'ref_pay': '04/15/2024'},
    'ADAML': {'spread': 0.0613,      'yahoo': 'ADAML',  'ref_ex': '04/01/2024', 'ref_pay': '04/15/2024'}
}

# --- 3. UI SETUP ---
st.set_page_config(page_title="3M Term SOFR Tracker", layout="wide")
st.title("📈 3-Month Term SOFR Preferreds")

row1_col1, row1_col2, row1_col3, _ = st.columns([1.5, 1.5, 1.5, 3])
with row1_col1:
    fwd_sofr = st.number_input("Current 3M Term SOFR (%)", value=3.67854, step=0.00001, format="%.5f")
with row1_col2:
    hist_sofr = st.number_input("Last Reset Term SOFR (%)", value=3.67854, step=0.00001, format="%.5f")
with row1_col3:
    increment_bps = st.number_input("Increment (BPS)", value=50, step=10)

st.markdown(
    f"<p style='font-size: 0.78rem; color: #808495; margin-top: -18px; margin-bottom: 20px;'>"
    f"Note: Rates may not reflect real-time CME fixings. Please verify and update Current and Last Reset values manually for precise results."
    f"</p>", 
    unsafe_allow_html=True
)

# --- 4. DATA PROCESSING ---
today = datetime.now()
main_rows = []
sens_rows = []
inc_dec = increment_bps / 10000  
target_rates = [(fwd_sofr/100) + (i * inc_dec) for i in range(-2, 3)]

for ticker, info in SOFR_DATA.items():
    try:
        price = float(yf.Ticker(info['yahoo']).history(period="1d")['Close'].iloc[-1])
    except: price = 25.0
    
    next_ex, next_pay = get_next_dates(info['ref_ex'], info['ref_pay'])
    prior_ex = next_ex - rd.relativedelta(months=3)
    
    curr_coupon_rate = (hist_sofr / 100) + info['spread']
    days_accrued = get_30_360_days(prior_ex, today.date())
    accrued = (25 * curr_coupon_rate) * (days_accrued / 360)
    
    fwd_coupon_rate = (fwd_sofr / 100) + info['spread']
    clean_p = price - accrued
    yld = (fwd_coupon_rate * 25) / clean_p if clean_p > 0 else 0

    main_rows.append({
        "Ticker": ticker,
        "Coupon (Locked)": round(curr_coupon_rate * 100, 2),
        "Price": price,
        "Accrued": accrued,
        "Full Qtr Div": (25 * curr_coupon_rate) / 4,
        "Clean Price": clean_p,
        "Curr Yield": yld * 100,
        "Spread (+CAS)": round(info['spread'] * 100, 2),
        "Next Ex-Div": next_ex,
        "Next Pay": next_pay
    })

    s_row = {"Ticker": ticker}
    for r in target_rates:
        label = f"{r*100:.2f}% SOFR"
        s_yld = ((r + info['spread']) * 25) / clean_p if clean_p > 0 else 0
        s_row[label] = s_yld * 100
    sens_rows.append(s_row)

# --- 5. RENDER DASHBOARD ---
st.subheader("Portfolio Performance")
st.dataframe(
    pd.DataFrame(main_rows), 
    use_container_width=True, 
    hide_index=True,
    column_config={
        "Coupon (Locked)": st.column_config.NumberColumn(format="%.2f%%"),
        "Price": st.column_config.NumberColumn(format="$%.2f"),
        "Accrued": st.column_config.NumberColumn(format="$%.3f"),
        "Full Qtr Div": st.column_config.NumberColumn(format="$%.3f"),
        "Clean Price": st.column_config.NumberColumn(format="$%.2f"),
        "Curr Yield": st.column_config.NumberColumn(format="%.2f%%"),
        "Spread (+CAS)": st.column_config.NumberColumn(format="%.2f%%"),
        "Next Ex-Div": st.column_config.DateColumn(format="MM/DD/YYYY"),
        "Next Pay": st.column_config.DateColumn(format="MM/DD/YYYY"),
    }
)

st.divider()
st.subheader(f"Yield Sensitivity (Forward @ {fwd_sofr:.5f}% SOFR)")
df_sens = pd.DataFrame(sens_rows)
sens_config = {col: st.column_config.NumberColumn(format="%.2f%%") for col in df_sens.columns if col != "Ticker"}
st.dataframe(df_sens, use_container_width=True, hide_index=True, column_config=sens_config)
