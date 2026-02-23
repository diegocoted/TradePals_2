import streamlit as st
from supabase import create_client
import pandas as pd
import requests
from datetime import datetime

# 1. Setup Page & Connection
st.set_page_config(page_title="Investor Agent", layout="wide")
st.title("🛰️ API Mission Control")

@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_connection()

# 2. Sidebar for API Management
with st.sidebar:
    st.header("API Configuration")
    finnhub_key = st.text_input("Finnhub API Key", type="password")
    st.info("Your keys are used only for this session and not stored in the DB.")

# 3. Price Testing Section
st.header("📈 Stock Price Tester")
ticker = st.text_input("Enter Ticker (e.g., AAPL, TSLA, NVDA):").upper()

if ticker:
    # --- STRATEGY: CHECK DATABASE FIRST ---
    res = supabase.table("price_cache").select("*").eq("ticker", ticker).order("fetched_at", desc=True).limit(1).execute()
    
    if res.data:
        st.write("✅ Found in Database (Saved an API call!)")
        st.dataframe(pd.DataFrame(res.data))
    else:
        st.warning("❌ Not in database. Ready to call API.")
        
    if st.button(f"Fetch Live Price for {ticker}"):
        if not finnhub_key:
            st.error("Please enter your Finnhub key in the sidebar first!")
        else:
            # --- CALL API ---
            url = f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={finnhub_key}"
            response = requests.get(url).json()
            
            if response.get('c'):
                price_data = {
                    "ticker": ticker,
                    "price": response['c'],
                    "volume": 0, # Quote API doesn't give volume, we'll fix later
                    "source": "Finnhub"
                }
                
                # --- SAVE TO DATABASE ---
                supabase.table("price_cache").insert(price_data).execute()
                
                # --- LOG THE CALL ---
                supabase.table("api_logs").insert({"api_name": "Finnhub", "endpoint": "quote", "was_cached": False}).execute()
                
                st.success(f"Price for {ticker} fetched and stored: ${response['c']}")
                st.rerun() # Refresh to show data from DB
            else:
                st.error("Invalid Ticker or API error.")

# 4. Database View
st.header("🗄️ Database Vault (Recent Activity)")
recent_data = supabase.table("price_cache").select("*").order("fetched_at", desc=True).limit(5).execute()
if recent_data.data:
    st.table(recent_data.data)
