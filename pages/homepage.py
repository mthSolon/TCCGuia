import streamlit as st
from helpers import fetch_cookies
class Homepage:
    cookies = fetch_cookies()
    st.title(f"Bem vindo {cookies['username']}!")