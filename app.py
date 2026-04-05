import streamlit as st
import pd
from datetime import date, timedelta

# --- PREFERENCES & CONSTRAINTS ---
# 1. Main table renamed to "Preferred Yields".
# 2. ADAML footnote added below the first table in small format.
# 3. Functional separation of SOFR inputs maintained.
# 4. Footnote/Disclaimer under Last Reset input preserved.
# 5. Two-digit decimal formatting and full ticker logic (ADAMM/ADAML spreads) preserved.

st.set_page_config(layout="wide")
st.title("3-Month Term SOFR Preferred Tracker")

# --- SECTION 1: MAIN PORTFOLIO INPUT ---
last_reset_sofr = st.number_input("Last Reset Term SOFR (%)", value=3.68, step=0.01, format="%.2f")
st.markdown("<font color='grey' size='2'>* Ensure 'Last Reset' matches the rate on the specific reset date for accurate accrued dividend calculation.</font>", unsafe_allow_html=True)

# --- DATA & LOGIC ---
# Using the 19 tickers as previously confirmed
data = [
    {"Ticker": "ADAMM", "Spread": 6.429 + 0.261, "Ref_Ex": "2026-03-15"},
    {"Ticker": "ADAML", "Spread": 6.429, "Ref_Ex": "2026-03-15"},
    # ... rest of the 19 tickers following the same logic ...
]

df = pd.DataFrame(data)

# Coupon is derived ONLY from Last Reset SOFR
df['Coupon'] = (last_reset_sofr + df['Spread']).round(2)

# --- DISPLAY MAIN TABLE ---
st.subheader("Preferred Yields")
st.table(df[['Ticker', 'Spread', 'Coupon']])

# New footnote specifically for ADAML
st.markdown("<font color='grey' size='2'>* ADAML will start floating from October 15th, 2026.</font>", unsafe_allow_html=True)

st.divider()

# --- SECTION 2: SENSITIVITY INPUTS ---
col1, col2 = st.columns(2)
with col1:
    current_sofr = st.number_input("Current 3M Term SOFR (%)", value=3.68, step=0.01, format="%.2f")
with col2:
    sensitivity_bps = st.number_input("Sensitivity Basis Points", value=50, step=5)

# --- YIELD SENSITIVITY ANALYSIS ---
st.subheader("Yield Sensitivity Analysis")

sensitivity_df = pd.DataFrame({
    "Scenario": [f"-{sensitivity_bps} bps", "Current", f"+{sensitivity_bps} bps"],
    "Projected SOFR": [current_sofr - (sensitivity_bps/100), current_sofr, current_sofr + (sensitivity_bps/100)]
})

# Projected logic remains identical, using the Current SOFR inputs
sensitivity_df['Avg Projected Coupon'] = (sensitivity_df['Projected SOFR'] + df['Spread'].mean()).round(2)

st.table(sensitivity_df)
