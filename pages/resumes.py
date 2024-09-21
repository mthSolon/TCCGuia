"""Class and methods to render resumes page"""

from time import time
import xml.dom.minidom
from collections import defaultdict
from typing import Dict, List, Optional

import requests
import pandas as pd
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile

from src.database import Database
from src.helpers import fetch_cookies, setup_database_connection


class ResumesFacade:
    """Class to perform parsing and similarity calculation with resumes"""

    def __init__(self, db, api_url, headers):
        self.db = db
        self.api_url = api_url
        self.headers = headers

    def _validate_theme_and_resumes(self, tcc_theme: Optional[str], resumes: Optional[List[UploadedFile]], professors: pd.DataFrame | None) -> bool:
        """Validate if the theme and resumes are None

        Args:
            tcc_theme (Optional[str]): TCC theme
            resumes (Optional[List[BytesIO]]): List of resumes

        Returns:
            bool: True if theme and resumes are valid, False otherwise.
        """
        if not tcc_theme:
            st.warning(":warning: Tema do TCC não pode ser em branco.")
            return False
        if professors is None:
            if not resumes:
                st.warning(":warning: É necessário fazer o upload de pelo menos 1 currículo.")
                return False
        return True

    def parse_resume(self, resumes: Optional[List[UploadedFile]]) -> Optional[Dict[str, List[str]]]:
        """Parse the XML resumes, get the specialities for every professor

        Args:
            resumes (List[BytesIO]): professors's resumes

        Returns:
            Dict[str, List[str]]: Dict containing the professor's name with his specialities.
        """
        professors = defaultdict(list)
        if resumes:
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
                    professors[nome_completo].append(especialidade)

            return professors

    def _calculate_similarity(self, professors: pd.DataFrame, tcc_theme: str) -> pd.DataFrame:
        """Calculate similarity between professors's and TCC theme strings.

        Args:
            professors (Dict[str, List[str]]): professors's names and specialities
            tcc_theme (str): TCC theme
        """
        scores = defaultdict(dict)
        if not professors.empty:
            for item in professors.to_dict(orient="records"):
                try:
                    scores_list = self._query_similarity({
                        "inputs": {
                            "source_sentence": f"{tcc_theme}",
                            "sentences": [area for area in item["areas_de_atuacao"]],
                        }
                    })
                except ConnectionRefusedError as e:
                    print(e)
                    st.error("Um problema com o modelo aconteceu :sadface:. Tente novamente em alguns minutos.")
                scores[item["nome"]] = max(scores_list) * 100
        professors_scores = pd.DataFrame.from_dict(scores, orient="index", columns=["Score"])
        professors_scores.index.name = "Professor"
        melhor_professor = professors_scores[professors_scores["Score"] == professors_scores["Score"].max()].index.values
        return professors_scores, melhor_professor
    
    def _query_similarity(self, payload: Dict[str, str], max_retries: int=5, delay: int=2) -> Dict[str, str]:
        """Performs query to BGE-M3 endpoint

        Args:
            payload (Dict[str, str]): payload to send
            retries (int): number of retries
            delay (int): delay to retry in seconds
        """
        retries = 0
        while retries < max_retries:
            response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=30)
            if response.ok:
                return response.json()
            else:
                print(f"Código 503 retornado, tentando novamente em {delay} segundos")
                time.sleep(delay)
        
        raise ConnectionRefusedError("Número de tentativas de conexão máxima excedida, modelo está indisponível.")

class ResumesPage:
    """Class to render resumes page"""

    def __init__(self) -> None:
        self.cookies = fetch_cookies()
        self.api_url = "https://api-inference.huggingface.co/models/BAAI/bge-m3"
        self.headers = {"Authorization": f"Bearer {st.secrets.api_token}"}
        if self.cookies.get("authentication_status") != "autorizado":
            st.switch_page("pages/login.py")
        if "db_connection" not in st.session_state:
            setup_database_connection()
            st.rerun()
        self.db: Database = st.session_state["db_connection"]
        self.facade = ResumesFacade(self.db, self.api_url, self.headers)
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
        st.info(":file_folder: No momento, apenas arquivos XML do Lattes são suportados")
        st.divider()
        professors_registered = self.db.read_professor(self.cookies["user_id"])
        theme_and_resumes_validated = self.facade._validate_theme_and_resumes(tcc_theme, resumes, professors_registered)

        if st.button("Sair"):
            self.cookies["authentication_status"] = "nao_autorizado"
            st.switch_page("main.py")

        if st.button("Sugerir professores") and theme_and_resumes_validated:
            with st.status("Aguarde...", expanded=True) as status:
                st.write("Processando currículos...")
                if resumes:
                    professors_resumes = self.facade.parse_resume(resumes)
                    st.write("Criando professores no banco de dados...")
                    professors_df: pd.DataFrame = self.db.create_professors(professors_resumes, self.cookies["user_id"])
                    if professors_registered is None:
                        professors_registered = professors_df
                    else:
                        professors_registered = professors_registered.concat([professors_df])
                if not professors_registered.empty:
                    st.write("Calculando similaridade...")
                    professors_scores, melhores_professores = self.facade._calculate_similarity(professors_registered, tcc_theme)
                    status.update(label="Concluído!", state="complete", expanded=False)
                else:
                    st.error("Ocorreu um erro. :confused:")
            if not professors_scores.empty:
                st.dataframe(professors_scores)
                st.write(f"Professor(es) com maior compatibilidade detectada:")
                for melhor_professor in melhores_professores:
                    st.write(f"- :green[**{melhor_professor}**]")    

    

    

    


ResumesPage()
