import streamlit as st

from database import Database


def main():
    st.set_page_config(
        page_title="TCCGuia",
        page_icon=":clipboard:",
        menu_items={'About': "# Feito por *Matheus R. O. Solon*"}
    )
    if "username" not in st.session_state:
        st.session_state["username"] = None
    if "authentication_status" not in st.session_state:
        st.session_state["authentication_status"] = None

    _setup_db_connection()
    st.title("Bem vindo ao :green[*TCCGuia*] :wave:")
    st.markdown(":green[TCCGuia] te ajudará a escolher seu professor orientador baseado no tema do seu TCC!")
    st.sidebar.page_link("pages/login.py", label="Já possuo uma conta")
    st.sidebar.page_link("pages/register.py", label="Não possui uma conta? Cadastre-se!")

@st.cache_resource
def _setup_db_connection():
    db = Database(**st.secrets.db_credentials)
    db.init_connection()
    if "db_connection" not in st.session_state:
        st.session_state["db_connection"] = db

if __name__ == "__main__":
    main()