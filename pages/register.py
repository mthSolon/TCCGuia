import streamlit as st
from main import _setup_db_connection
from database import Database
from helpers import fetch_cookies
from src.hasher import Hasher
from typing import Union


class RegisterPage:
    def __init__(self) -> None:
        self.cookies = fetch_cookies()
        if "db_connection" not in st.session_state:
            _setup_db_connection()
            st.rerun()
        self.db: Database = st.session_state["db_connection"]
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
        _, username, _ = self.db.read_user(self.email)
        if username:
            self.cookies["authentication_status"] = "nao_autorizado"
            return "Usuário com este email já está cadastrado"
        self.password = Hasher.hash_pw(self.password)
        user_id = self.db.create_user(self.username, self.email, self.password)
        if user_id:
            self.cookies["username"] = self.username
            self.cookies["user_id"] = str(user_id)
            self.cookies["authentication_status"] = "autorizado"
            return True
        else:
            self.cookies["authentication_status"] = "nao_autorizado"
            return "Ocorreu um erro"
RegisterPage()