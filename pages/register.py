import streamlit as st

from database import Database
from src.hasher import Hasher


class RegisterPage:
    def __init__(self) -> None:
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
            self._register_user()
            if st.session_state["authentication_status"] == None:
                st.warning("Por favor, preencha os campos necessários.")
            if st.session_state["authentication_status"] == False:
                st.error("Ocorreu um erro.")
            if st.session_state["authentication_status"] == True:
                st.switch_page("pages/login.py")


    def _register_user(self) -> bool:
        if not (self.username or self.email or self.password):
            st.session_state["authentication_status"] = None
            return None
        self.password = Hasher.hash_pw(self.password)
        status = self.db.insert_user(self.username, self.email, self.password)
        if status:
            st.session_state["username"] = self.username
            st.session_state["authentication_status"] = True
            return True
        else:
            st.session_state["authentication_status"] = False
            return False
RegisterPage()