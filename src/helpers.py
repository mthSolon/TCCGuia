"""Helpers functions"""

import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager

from database import Database

def fetch_cookies():
    """Fetch the stored cookies"""
    cookies = EncryptedCookieManager(prefix="tccguia/", password=st.secrets.cookies_credentials)

    if not cookies.ready():
        st.stop()
    return cookies

def setup_database_connection():
    """Instantiate database connection"""

    db = Database()
    if "db_connection" not in st.session_state:
        st.session_state["db_connection"] = db