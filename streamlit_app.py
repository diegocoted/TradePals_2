import streamlit as st
from supabase import create_client
import pandas as pd
import requests
from datetime import datetime, timedelta

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
    marketaux_key = st.text_input("Marketaux API Key", type="password")
    st.info("Keys are session-only and not stored in your DB.")

# --- PRICE TESTER ---
st.header("📈 Stock Price Tester")
ticker = st.text_input("Enter Ticker (e.g., AAPL):").upper()

if ticker:
    res = supabase.table("price_cache").select("*").eq("ticker", ticker).order("fetched_at", desc=True).limit(1).execute()
    if res.data:
        st.write("✅ Found Price in Database")
        st.table(res.data)
    
    if st.button(f"Fetch Live Price for {ticker}"):
        if finnhub_key:
            url = f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={finnhub_key}"
            r = requests.get(url).json()
            if r.get('c'):
                supabase.table("price_cache").insert({"ticker": ticker, "price": r['c'], "source": "Finnhub"}).execute()
                st.rerun()
        else:
            st.error("Missing Finnhub Key")

# --- NEWS & RESEARCH CENTER ---
st.header("📰 News & Knowledge Center")
tab1, tab2, tab3 = st.tabs(["Company News (Finnhub)", "Macro News (Marketaux)", "🕵️ Agent Research"])

with tab1:
    if ticker:
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        db_news = supabase.table("news_vault").select("*").eq("ticker", ticker).gt("fetched_at", yesterday).execute()
        
        if db_news.data:
            st.write(f"✅ Showing {len(db_news.data)} articles from Database")
            st.dataframe(pd.DataFrame(db_news.data)[['headline', 'fetched_at', 'provider_url']])
        else:
            st.info("No recent news in DB for this ticker.")
            
        if st.button(f"Pull News for {ticker}"):
            if finnhub_key:
                end = datetime.now().strftime('%Y-%m-%d')
                start = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                url = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from={start}&to={end}&token={finnhub_key}"
                news_data = requests.get(url).json()
                
                for item in news_data[:5]:
                    supabase.table("news_vault").upsert({
                        "ticker": ticker,
                        "headline": item['headline'],
                        "content": item['summary'],
                        "provider_url": item['url'],
                        "source": "Finnhub"
                    }, on_conflict='provider_url').execute()
                st.rerun()

with tab2:
    theme = st.text_input("Macro Theme (e.g., Inflation, AI, Fed):")
    if theme and st.button("Search Macro News"):
        if marketaux_key:
            url = f"https://api.marketaux.com/v1/news/all?search={theme}&api_token={marketaux_key}&language=en"
            macro_data = requests.get(url).json()
            
            if 'data' in macro_data:
                for item in macro_data['data'][:3]:
                    supabase.table("news_vault").upsert({
                        "headline": item['title'],
                        "content": item['description'],
                        "provider_url": item['url'],
                        "source": "Marketaux"
                    }, on_conflict='provider_url').execute()
                st.success(f"Stored macro news for '{theme}'")
                st.rerun()

with tab3:
    st.subheader("Deep Intelligence Log")
    st.write("Use this section to manually feed the agent deep research data (10-Ks, competitor analysis, etc.)")
    
    col1, col2 = st.columns(2)
    with col1:
        res_ticker = st.text_input("Research Ticker:", key="res_tick").upper()
        res_topic = st.selectbox("Intelligence Type:", ["Competitors", "10-K Summary", "Product Roadmap", "Sector Analysis"])
    with col2:
        res_url = st.text_input("Source URL:")
    
    res_content = st.text_area("Research Findings / Deep Text Content:", height=200)
    
    if st.button("Commit to Knowledge Bank"):
        if res_ticker and res_content:
            supabase.table("research_notes").insert({
                "ticker": res_ticker,
                "topic": res_topic,
                "content": res_content,
                "source_url": res_url
            }).execute()
            st.success(f"Stored {res_topic} for {res_ticker}!")
            st.rerun()
        else:
            st.error("Ticker and Content are required to build the Knowledge Bank.")

# 4. Database View
st.header("🗄️ Database Vault (Recent Knowledge)")
res_history = supabase.table("research_notes").select("*").order("created_at", desc=True).limit(5).execute()
if res_history.data:
    st.write("### Recent Research Notes")
    st.table(res_history.data)

all_news = supabase.table("news_vault").select("headline", "source", "fetched_at").order("fetched_at", desc=True).limit(10).execute()
if all_news.data:
    st.write("### Recent News Articles")
    st.table(all_news.data)
