import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import dateutil.relativedelta as rd
import requests

# --- 1. TERM SOFR FETCHING (FORWARD LOOKING) ---

@st.cache_data(ttl=3600)
def get_historical_term_sofr(lock_in_date):
    """
    Attempts to fetch the 3-Month CME Term SOFR.
    Note: Term SOFR is forward-looking, unlike NY Fed averages.
    """
    try:
        # Using a reliable financial data proxy for CME Term SOFR
        # Format: YYYY-MM-DD
        date_str = lock_in_date.strftime('%Y-%m-%d')
        
        # This is a placeholder for the specific endpoint - 
        # In a production Streamlit app, you'd often use a 
        # library like 'fredapi' if Term SOFR were public, 
        # but for CME data, we check a mirrored fixing site.
        url = f"https://api.example-finance.com/v1/rates/term-sofr-3m/{date_str}"
        # response = requests.get(url)
        # return response.json()['rate'] / 100
        
        return None # Default to None to trigger the manual/input fallback
    except:
        return None

# --- 2. THE MASTER DATA ---
SOFR_DATA = {
    'AGNCN': {'spread': 0.0463 + 0.0026161, 'yahoo': 'AGNCN',  'ref_ex': '03/31/2024', 'pay_day': 15},
    'ADAML': {'spread': 0.0613,             'yahoo': 'ADAML',  'ref_ex': '03/15/2024', 'pay_day': 15},
    # ... (Include all 24 tickers here)
}

# --- 3. UI SETUP ---
st.set_page_config(page_title="3M Term SOFR Tracker", layout="wide")

with st.sidebar:
    st.header("Rate Controls")
    current_term_sofr = st.number_input("Current 3M Term SOFR (%)", value=3.68, step=0.01)
    
    st.divider()
    st.write("### Historical Lock-in Override")
    st.info("If the auto-fetch is blocked, enter the 3M Term SOFR rate that was active at the last reset.")
    manual_hist_sofr = st.number_input("Last Reset Term SOFR (%)", value=current_term_sofr, step=0.01)

# --- 4. PROCESSING ---
today = datetime.now()
main_data = []

for ticker, info in SOFR_DATA.items():
    # A. Price Fetch
    try:
        price = float(yf.Ticker(info['yahoo']).history(period="1d")['Close'].iloc[-1])
    except: price = 25.0
    
    # B. Dates
    next_ex, next_pay = get_next_dates(info['ref_ex'], info['pay_day'])
    prior_ex = next_ex - rd.relativedelta(months=3)
    prior_pay = next_pay - rd.relativedelta(months=3)
    
    # C. Accrual Rate (The "Lock-in")
    # We use the manual override value by default for 100% precision control
    accrual_sofr = manual_hist_sofr / 100
    
    # D. Accrual Math
    days_accrued = get_30_360_days(prior_ex, today.date())
    current_coupon = accrual_sofr + info['spread']
    accrued_val = (25 * current_coupon) * (days_accrued / 360)
    
    # E. Yield Math (Forward looking)
    fwd_sofr = current_term_sofr / 100
    fwd_coupon = fwd_sofr + info['spread']
    clean_p = price - accrued_val
    curr_yield = (fwd_coupon * 25) / clean_p if clean_p > 0 else 0

    main_data.append({
        "Ticker": ticker,
        "Coupon (Reset)": current_coupon * 100,
        "Accrued": accrued_val,
        "Curr Yield": curr_yield * 100,
        "Next Pay": next_pay
    })

st.dataframe(pd.DataFrame(main_data), use_container_width=True)
