"""Class and methods to render register page"""

from typing import Union

import streamlit as st
from src.database import Database
from src.hasher import Hasher
from src.helpers import fetch_cookies


class RegisterPage:
    """Class to render register page"""

    def __init__(self) -> None:
        self.cookies = fetch_cookies()
        self.db: Database = Database.get_instance()
        self._render_register_page()

    def _render_register_page(self) -> None:
        """Render register page"""
        register_form = st.form("Cadastro")
        register_form.subheader("Crie uma conta")
        self.username = register_form.text_input("Nome")
        self.email = register_form.text_input("E-mail")
        self.password = register_form.text_input("Senha", type="password")
        if st.button("Já possuo uma conta"):
            st.switch_page("pages/login.py")
        if register_form.form_submit_button("Cadastrar"):
            msg = self._register_user()
            if self.cookies["authentication_status"] == "dados_invalidos":
                st.warning(msg)
            elif self.cookies["authentication_status"] == "nao_autorizado":
                st.error(msg)
            elif self.cookies["authentication_status"] == "autorizado":
                st.switch_page("pages/resumes.py")

    def _register_user(self) -> Union[bool, str]:
        """Register user

        Returns:
            Union[bool, str]: True if the user was registered, str if wasn't
        """
        if not (self.username and self.email and self.password):
            self.cookies["authentication_status"] = "dados_invalidos"
            return "Por favor, preencha os campos necessários."
        user = self.db.read_user(self.email)
        if not user.empty:
            self.cookies["authentication_status"] = "nao_autorizado"
            return "Usuário com este email já está cadastrado"
        hashed_pw = Hasher.hash_pw(self.password)
        user = self.db.create_user(self.username, self.email, hashed_pw)
        if not user.empty:
            self.cookies["username"] = self.username
            self.cookies["user_id"] = str(user.at[0, "id"])
            self.cookies["authentication_status"] = "autorizado"
            return True
        else:
            self.cookies["authentication_status"] = "nao_autorizado"
            return "Ocorreu um erro"


RegisterPage()
