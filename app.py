import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import dateutil.relativedelta as rd

# --- 1. SOFR DATA ENGINE ---
# Applied Logic: Spread + 0.26161% (CAS) for LIBOR-transitioned tickers.
# ADAML (6.13%) stays native as it was issued as a SOFR security.
SOFR_DATA = {
    'AGNCP': {'spread': 0.0510 + 0.0026161, 'yahoo': 'AGNCP',  'ref_ex': '03/01/2024', 'pay_day': 15},
    'NLY-F': {'spread': 0.0499 + 0.0026161, 'yahoo': 'NLY-PF', 'ref_ex': '03/01/2024', 'pay_day': 15},
    'NLY-G': {'spread': 0.0417 + 0.0026161, 'yahoo': 'NLY-PG', 'ref_ex': '02/28/2024', 'pay_day': 15},
    'NLY-I': {'spread': 0.0499 + 0.0026161, 'yahoo': 'NLY-PI', 'ref_ex': '03/01/2024', 'pay_day': 15},
    'PMT-C': {'spread': 0.0507 + 0.0026161, 'yahoo': 'PMT-PC', 'ref_ex': '02/28/2024', 'pay_day': 15},
    'ADAML': {'spread': 0.0613,            'yahoo': 'ADAML',  'ref_ex': '03/15/2024', 'pay_day': 15}
}

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

# --- 2. UI SETUP ---
st.set_page_config(page_title="3M SOFR Tracker", layout="wide")
st.title("📈 3-Month Term SOFR Preferreds")

col_a, col_b, _ = st.columns([1.5, 1.5, 3])
with col_a:
    sofr_rate = st.number_input("Current 3M Term SOFR (%)", value=3.68, step=0.01)
with col_b:
    increment_bps = st.number_input("Increment (Basis Points)", value=50, step=10)

inc_dec = increment_bps / 10000  
today = datetime.now()

# 3. CALCULATIONS
main_data = []
sens_data = []
target_rates = [(sofr_rate/100) + (i * inc_dec) for i in range(-2, 3)]

for ticker, info in SOFR_DATA.items():
    try:
        price = float(yf.Ticker(info['yahoo']).history(period="1d")['Close'].iloc[-1])
    except:
        price = 25.0
    
    next_ex, next_pay = get_next_dates(info['ref_ex'], info['pay_day'])
    prior_ex = next_ex - rd.relativedelta(months=3)
    days_accrued = get_30_360_days(prior_ex, today.date())
    
    current_coupon = (sofr_rate/100) + info['spread']
    accrued_val = (25 * current_coupon) * (days_accrued / 360)
    clean_p = price - accrued_val
    curr_yield = (current_coupon * 25) / clean_p if clean_p > 0 else 0

    main_data.append({
        "Ticker": ticker,
        "Current Coupon": current_coupon * 100,
        "Price": price,
        "Accrued": accrued_val,
        "Full Qtr Div": (25 * current_coupon) / 4,
        "Clean Price": clean_p,
        "Curr Yield": curr_yield * 100,
        "Spread (+CAS)": info['spread'] * 100,
        "Next Ex-Div": next_ex,
        "Next Pay": next_pay
    })

    sens_row = {"Ticker": ticker}
    for r in target_rates:
        label = f"{r*100:.2f}% SOFR"
        s_yield = ((r + info['spread']) * 25) / clean_p if clean_p > 0 else 0
        sens_row[label] = s_yield * 100
    sens_data.append(sens_row)

# 4. RENDER
st.subheader("Sortable SOFR Dashboard")
st.dataframe(
    pd.DataFrame(main_data),
    use_container_width=True,
    hide_index=True,
    column_config={
        "Current Coupon": st.column_config.NumberColumn(format="%.2f%%"),
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

st.subheader(f"Yield Sensitivity Analysis (Centered @ {sofr_rate:.2f}%)")
df_sens = pd.DataFrame(sens_data)
sens_config = {col: st.column_config.NumberColumn(format="%.2f%%") for col in df_sens.columns if col != "Ticker"}
st.dataframe(df_sens, use_container_width=True, hide_index=True, column_config=sens_config)
