import streamlit as st
from database import Database
from helpers import fetch_cookies
from main import _setup_db_connection
from src.hasher import Hasher
from typing import Union


class LoginPage:
    def __init__(self):
        self.cookies = fetch_cookies()
        if self.cookies.get("authentication_status") == "autorizado":
            st.switch_page("pages/resumes.py")
        if "db_connection" not in st.session_state:
            _setup_db_connection()
            st.rerun()
        self.db: Database = st.session_state["db_connection"]
        self._render_login_page()

    def _render_login_page(self) -> None:
        """Render the login page"""
        login_form = st.form("Login")
        login_form.subheader("Acesse sua conta")
        self.email = login_form.text_input("E-mail")
        self.password = login_form.text_input("Senha", type="password")
        if st.button("Não possui uma conta? Cadastre-se!"):
            st.switch_page("pages/register.py")
        if login_form.form_submit_button("Entrar"):
            msg = self._check_credentials()
            if self.cookies["authentication_status"] == "dados_invalidos":
                st.warning(msg)
            elif self.cookies["authentication_status"] == "nao_autorizado":
                st.error(msg)
            elif self.cookies["authentication_status"] == "autorizado":
                st.switch_page("pages/resumes.py")

    def _check_credentials(self) -> Union[bool, str]:
        """Check if the user credentials are valid

        Returns:
            Union[bool, str]: True if is valid, str otherwise
        """
        if not (self.email and self.password):
            self.cookies["authentication_status"] = "dados_invalidos"
            return "Por favor, preencha os campos necessários."
        user_id, username, user_pw = self.db.read_user(self.email)
        if user_id and Hasher.check_pw(user_pw, self.password):
            self.cookies["username"] = username
            self.cookies["user_id"] = str(user_id)
            self.cookies["authentication_status"] = "autorizado"
            return True
        else:
            self.cookies["authentication_status"] = "nao_autorizado"
            return "E-mail ou senha incorretos."

LoginPage()