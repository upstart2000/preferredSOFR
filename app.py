import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import dateutil.relativedelta as rd
import pandas_datareader.data as web

# --- 1. DATA FETCHING HELPERS ---

@st.cache_data(ttl=3600)
def get_historical_sofr(lock_in_date):
    """Fetches historical 3M Term SOFR from FRED for the Rate Lock-in."""
    try:
        # Buffer to find the last available business day
        start = lock_in_date - timedelta(days=7)
        df = web.DataReader('SOFR3M', 'fred', start, lock_in_date)
        return df.iloc[-1][0] / 100 
    except:
        return None

def get_next_dates(ref_ex_str, pay_day_target):
    """Calculates the cycle of Ex-Dates and Payment Dates."""
    today = datetime.now()
    current_ex = datetime.strptime(ref_ex_str, '%m/%d/%Y')
    while current_ex <= today:
        current_ex += rd.relativedelta(months=3)
    next_pay = current_ex.replace(day=pay_day_target)
    if next_pay < current_ex:
        next_pay += rd.relativedelta(months=1)
    return current_ex.date(), next_pay.date()

def get_30_360_days(start, end):
    """US 30/360 Day Count Convention."""
    d1 = min(start.day, 30)
    d2 = 30 if (d1 >= 30 and end.day == 31) else end.day
    if start.month == 2 and (start + timedelta(days=1)).month == 3: d1 = 30
    if end.month == 2 and (end + timedelta(days=1)).month == 3: d2 = 30
    return (end.year - start.year) * 360 + (end.month - start.month) * 30 + (d2 - d1)

# --- 2. MASTER DATASET ---
# Note: CAS (0.0026161) added to all except ADAM family
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

# --- 3. UI SETUP ---
st.set_page_config(page_title="3M SOFR Tracker", layout="wide")
st.title("📈 3-Month Term SOFR Preferred Portfolio")

col_a, col_b, _ = st.columns([1.5, 1.5, 3])
with col_a:
    sofr_rate = st.number_input("Current 3M Term SOFR (%)", value=3.68, step=0.01)
with col_b:
    increment_bps = st.number_input("Increment (Basis Points)", value=50, step=10)

inc_dec = increment_bps / 10000  
today = datetime.now()

# 4. PROCESSING
main_data = []
sens_data = []
target_rates = [(sofr_rate/100) + (i * inc_dec) for i in range(-2, 3)]

for ticker, info in SOFR_DATA.items():
    try:
        price = float(yf.Ticker(info['yahoo']).history(period="1d")['Close'].iloc[-1])
    except:
        price = 25.0
    
    # DATE ANCHORS
    next_ex, next_pay = get_next_dates(info['ref_ex'], info['pay_day'])
    prior_ex = next_ex - rd.relativedelta(months=3)
    prior_pay = next_pay - rd.relativedelta(months=3)
    
    # 1. RATE LOCK-IN: Use 1 business day prior to the LAST PAYMENT DATE
    lock_in_target = prior_pay - timedelta(days=1)
    hist_sofr = get_historical_sofr(lock_in_target)
    effective_sofr = hist_sofr if hist_sofr is not None else (sofr_rate / 100)
    
    # 2. ACCRUAL PERIOD: Use Prior Ex-Date to Today
    days_accrued = get_30_360_days(prior_ex, today.date())
    
    # CALCULATIONS
    current_coupon = effective_sofr + info['spread']
    accrued_val = (25 * current_coupon) * (days_accrued / 360)
    clean_p = price - accrued_val
    curr_yield = (current_coupon * 25) / clean_p if clean_p > 0 else 0

    main_data.append({
        "Ticker": ticker,
        "Coupon (Locked)": current_coupon * 100,
        "Price": price,
        "Accrued": accrued_val,
        "Full Qtr Div": (25 * current_coupon) / 4,
        "Clean Price": clean_p,
        "Curr Yield": curr_yield * 100,
        "Spread (+CAS)": info['spread'] * 100,
        "Next Ex-Div": next_ex,
        "Next Pay": next_pay
    })

    # SENSITIVITY (Based on Current Input SOFR)
    sens_row = {"Ticker": ticker}
    for r in target_rates:
        label = f"{r*100:.2f}% SOFR"
        s_yield = ((r + info['spread']) * 25) / clean_p if clean_p > 0 else 0
        sens_row[label] = s_yield * 100
    sens_data.append(sens_row)

# 5. RENDER TABLES
st.subheader("Sortable SOFR Dashboard")
st.dataframe(
    pd.DataFrame(main_data),
    use_container_width=True,
    hide_index=True,
    column_config={
        "Coupon (Locked)": st.column_config.NumberColumn(format="%.2f%%"),
        "Price": st.column_config.NumberColumn(format="$%.2f"),
        "Accrued": st.column_config.NumberColumn(format="$%.3f"),
        "Full Qtr Div": st.column_config.NumberColumn(format="$%.3f"),
        "Clean Price": st.column_config.NumberColumn(format="$%.2f"),
        "Curr Yield": st.column_config.NumberColumn(format="%.2f%%"),
        "Spread (+CAS)": st.column_config.NumberColumn(format="%.4f%%"),
        "Next Ex-Div": st.column_config.DateColumn(format="MM/DD/YYYY"),
        "Next Pay": st.column_config.DateColumn(format="MM/DD/YYYY"),
    }
)

st.divider()

st.subheader(f"Yield Sensitivity Analysis (Centered @ {sofr_rate:.2f}% SOFR)")
df_sens = pd.DataFrame(sens_data)
sens_config = {col: st.column_config.NumberColumn(format="%.2f%%") for col in df_sens.columns if col != "Ticker"}
st.dataframe(df_sens, use_container_width=True, hide_index=True, column_config=sens_config)
