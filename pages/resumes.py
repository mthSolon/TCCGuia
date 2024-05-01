"""Class and methods to render resumes page"""

import xml.dom.minidom
from collections import defaultdict
from io import BytesIO
from typing import Dict, List, Optional

import requests
import streamlit as st
from src.database import Database
from src.helpers import fetch_cookies, setup_db_connection


class ResumesPage:
    """Class to render resumes page"""

    def __init__(self) -> None:
        self.API_URL = "https://api-inference.huggingface.co/models/BAAI/bge-m3"
        self.headers = {"Authorization": f"Bearer {st.secrets.api_token}"}
        self.cookies = fetch_cookies()
        if self.cookies.get("authentication_status") != "autorizado":
            st.switch_page("pages/login.py")
        if "db_connection" not in st.session_state:
            setup_db_connection()
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
            type="xml",
        )
        st.info(
            ":file_folder: No momento, apenas arquivos XML do Lattes são suportados"
        )
        st.divider()
        theme_and_resumes_validated = ResumesPage._validate_theme_and_resumes(
            tcc_theme, resumes
        )
        if st.button("Sugerir professores") and theme_and_resumes_validated:
            with st.status("Aguarde...", expanded=True) as status:
                st.write("Processando currículos...")
                professors = self.read_resume(resumes)
                st.write("Criando professores no banco de dados...")
                exists = self.db.create_professors(professors, self.cookies["user_id"])
                if exists:
                    st.write("Calculando similaridade...")
                    professors_scores = self._calculate_similarity(
                        professors, tcc_theme
                    )
                    status.update(label="Concluído!", state="complete", expanded=False)
                else:
                    st.error("Ocorreu um erro. :confused:")
            st.write(professors_scores) if professors_scores else None

    def _calculate_similarity(
        self, professors: Dict[str, List[str]], tcc_theme: str
    ) -> defaultdict:
        """Calculate similarity between professors's and TCC theme strings.

        Args:
            professors (Dict[str, List[str]]): professors's names and specialities
            tcc_theme (str): TCC theme
        """
        scores = defaultdict(dict)
        for professor, specialities in professors.items():
            scores_list = self._query(
                {
                    "inputs": {
                        "source_sentence": f"{tcc_theme}",
                        "sentences": [speciality for speciality in specialities],
                    }
                }
            )
            scores[professor] = {
                speciality: score
                for speciality, score in zip(specialities, scores_list)
            }
        return scores

    def _query(self, payload) -> Dict[str, str]:
        """Performs query to BGE-M3 endpoint

        Args:
            payload (Dict[str, str]): payload to send
        """
        response = requests.post(self.API_URL, headers=self.headers, json=payload)
        return response.json()

    @staticmethod
    def _validate_theme_and_resumes(
        tcc_theme: Optional[str], resumes: Optional[List[BytesIO]]
    ) -> bool:
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
            st.warning(
                ":warning: É necessário fazer o upload de pelo menos 1 currículo."
            )
        elif tcc_theme and resumes:
            return True
        return False

    def read_resume(self, resumes: List[BytesIO]) -> Dict[str, List[str]]:
        """Parse the XML resumes, get the specialities for every professor

        Args:
            resumes (List[BytesIO]): professors's resumes

        Returns:
            Dict[str, List[str]]: Dict containing the professor's name with his specialities.
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
                    especialidade = area.getAttribute(
                        "NOME-DA-SUB-AREA-DO-CONHECIMENTO"
                    )
                    if especialidade == "":
                        especialidade = area.getAttribute(
                            "NOME-DA-AREA-DO-CONHECIMENTO"
                        )
                professors[nome_completo].append(especialidade)

        return professors


ResumesPage()
