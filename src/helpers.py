"""Helpers functions"""

import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager
from src.database import Database


def setup_db_connection():
    """Setup the database connection and stores at session state"""
    db = Database(**st.secrets.db_credentials)
    db.init_connection()
    if "db_connection" not in st.session_state:
        st.session_state["db_connection"] = db


def fetch_cookies():
    """Fetch the stored cookies"""
    cookies = EncryptedCookieManager(
        prefix="tccguia/", password=st.secrets.cookies_credentials
    )

    if not cookies.ready():
        st.stop()
    return cookies