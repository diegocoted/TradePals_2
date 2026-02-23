import streamlit as st
from supabase import create_client

st.title("🚀 Autonomous Investor Agent: Mission Control")

# Connection to Supabase
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_connection()
    st.success("Connected to Supabase Vault!")
except Exception as e:
    st.error(f"Waiting for API keys... {e}")

st.write("This dashboard will monitor your API calls and database storage.")