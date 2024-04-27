"""Class and methods to render resumes page"""

from typing import Dict, List, Optional
from collections import defaultdict
from io import BytesIO
import xml.dom.minidom
import streamlit as st
from src.database import Database
from src.helpers import setup_db_connection, fetch_cookies
from FlagEmbedding import BGEM3FlagModel


class ResumesPage:
    """Class to render resumes page"""

    def __init__(self) -> None:
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
            professors = self.read_resume(resumes)
            # status = self.db.create_professors(professors, self.cookies["user_id"])
            ResumesPage._calculate_similarity(professors, tcc_theme)

            # if status:
            #     pass
            # else:
            #     st.error("Ocorreu um erro. :confused:")

    @staticmethod
    def _calculate_similarity(professors: Dict[str, List[str]], tcc_theme: str):
        """Calculate the semantic similarities between professors's specialities and TCC theme
        using the BGE-M3 algorithm.

        Args:
            tcc_theme(Optional[str]): TCC theme
            professors (Dict[str, List[str]]): professors
        """
        colbert_scores = defaultdict(list)
        model = BGEM3FlagModel("BAAI/bge-m3", use_fp16=True)
        for professor, specialities in professors.items():
            for speciality in specialities:
                output_1 = model.encode(
                    tcc_theme, return_sparse=True, return_colbert_vecs=True
                )
                output_2 = model.encode(
                    speciality, return_sparse=True, return_colbert_vecs=True
                )
                colbert_score = model.colbert_score(
                    output_1["colbert_vecs"], output_2["colbert_vecs"]
                )
                colbert_scores[professor].append({speciality: colbert_score})
        return st.write(colbert_scores)

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
        """Parse the XML resumes, get the specialties for every professor

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
