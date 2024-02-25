import streamlit as st

from src.hasher import Hasher


class LoginPage:
    def __init__(self):
        if st.session_state.get("authentication_status"):
            st.switch_page("pages/homepage.py")
        self.db = st.session_state["db_connection"]
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
            self._check_credentials()
            if st.session_state["authentication_status"] == None:
                st.warning("Por favor, preencha os campos necessários.")
            if st.session_state["authentication_status"] == False:
                st.error("E-mail ou senha incorretos.")
            if st.session_state["authentication_status"] == True:
                st.switch_page("pages/homepage.py")

    def _check_credentials(self) -> bool:
        """Check if the user credentials are valid

        Returns:
            bool: True if is valid, False otherwise
        """
        if not (self.email and self.password):
            st.session_state["authentication_status"] = None
            return None
        user, user_pw = self.db.check_user(self.email)
        if user and Hasher.check_pw(user_pw, self.password):
            st.session_state["username"] = user
            st.session_state["authentication_status"] = True
            return True
        else:
            st.session_state["authentication_status"] = False
            return False

LoginPage()