"""Class and methods to render login page"""

from typing import Union

import streamlit as st
from src.database import Database
from src.hasher import Hasher
from src.helpers import fetch_cookies


class LoginPage:
    """Class to render login page"""

    def __init__(self):
        self.cookies = fetch_cookies()
        if self.cookies.get("authentication_status") == "autorizado":
            st.switch_page("pages/resumes.py")
        self.db: Database = Database.get_instance()
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
        user = self.db.read_user(self.email)
        if not user.empty and Hasher.check_pw(user.at[0, "senha"], self.password):
            self.cookies["username"] = user.at[0, "username"]
            self.cookies["user_id"] = str(user.at[0, "id"])
            self.cookies["authentication_status"] = "autorizado"
            return True
        else:
            self.cookies["authentication_status"] = "nao_autorizado"
            return "E-mail ou senha incorretos."


LoginPage()
