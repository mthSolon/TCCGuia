"""Module that starts the project"""

import streamlit as st

def main():
    """Main function that initializes the necessary modules"""
    st.set_page_config(
        page_title="TCCGuia",
        page_icon=":clipboard:",
        menu_items={"About": "# Feito por *Matheus R. O. Solon*"},
    )

    st.title("Bem vindo ao :green[*TCCGuia*] :wave:")
    st.markdown(
        ":green[TCCGuia] te ajudará a escolher seu professor orientador baseado no tema do seu TCC!"
    )
    st.sidebar.page_link("pages/login.py", label="Já possuo uma conta")
    st.sidebar.page_link(
        "pages/register.py", label="Não possui uma conta? Cadastre-se!"
    )


if __name__ == "__main__":
    main()
