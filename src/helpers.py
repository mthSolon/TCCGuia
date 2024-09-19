"""Helpers functions"""

import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager

def fetch_cookies():
    """Fetch the stored cookies"""
    cookies = EncryptedCookieManager(prefix="tccguia/", password=st.secrets.cookies_credentials)

    if not cookies.ready():
        st.stop()
    return cookies
