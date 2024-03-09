import streamlit as st
import xml.dom.minidom
from collections import defaultdict
from database import Database
from io import BytesIO
from typing import Dict, List, Optional
from helpers import _setup_db_connection, fetch_cookies


class ResumesPage:
    def __init__(self) -> None:
        self.cookies = fetch_cookies()
        if self.cookies.get("authentication_status") != "autorizado":
            st.switch_page("pages/login.py")
        if "db_connection" not in st.session_state:
            _setup_db_connection()
            st.rerun()
        self.db: Database = st.session_state["db_connection"]
        self._render_resumes_page()
    
    def _render_resumes_page(self):
        """Render the resumes page"""
        tcc_theme = st.text_input("Digite o tema do seu TCC abaixo :point_down:")
        st.divider()
        resumes = st.file_uploader(
            "Faça o upload dos currículos dos professores :point_down:",
            accept_multiple_files=True,
            type="xml"
            )
        st.info(":file_folder: No momento, apenas arquivos XML do Lattes são suportados")
        st.divider()
        if st.button("Sugerir professores") and ResumesPage._validate_theme_and_resumes(tcc_theme, resumes):
            professors = self.read_resume(resumes)
            status = self.db.create_professors(professors, self.cookies["user_id"])
            if status:
                st.success("Professores registrados")
            else:
                st.error("Ocorreu um erro. :confused:")
            

    @staticmethod
    def _validate_theme_and_resumes(tcc_theme: Optional[str], resumes: Optional[List[BytesIO]]) -> bool:
        """Validate if the theme and resumes are None

        Args:
            tcc_theme (Optional[str]): TCC theme
            resumes (Optional[List[BytesIO]]): List of resumes

        Returns:
            bool: True if theme and resumes are valid, False otherwise.
        """
        if not tcc_theme:
            st.warning(":warning: Tema do TCC não pode ser em branco.")
        if not resumes:
            st.warning(":warning: É necessário fazer o upload de pelo menos 1 currículo.")
        elif tcc_theme and resumes:
            return True
        return False

    def read_resume(self, resumes: List[BytesIO]) -> Dict[str, List[str]]:
        """Parse the XML resumes, get the specialties for every professor

        Args:
            resumes (List[BytesIO]): professors's resumes

        Returns:
            Dict[str, List[str]]: Dict containing the professor's name with his specialties.
        """
        professors = defaultdict(list)
        for resume in resumes:
            curriculo = xml.dom.minidom.parse(resume)
            dados_gerais = curriculo.getElementsByTagName("DADOS-GERAIS")
            nome_completo = dados_gerais[0].getAttribute("NOME-COMPLETO")
            areas_de_atuacao = curriculo.getElementsByTagName("AREA-DE-ATUACAO")
            for area in areas_de_atuacao:
                especialidade = area.getAttribute("NOME-DA-ESPECIALIDADE")
                if especialidade == "":
                    especialidade = area.getAttribute("NOME-DA-SUB-AREA-DO-CONHECIMENTO")
                    if especialidade == "":
                        especialidade = area.getAttribute("NOME-DA-AREA-DO-CONHECIMENTO")
                    pass
                professors[nome_completo].append(especialidade)
            
        return professors


ResumesPage()