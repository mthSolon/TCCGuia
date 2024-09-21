"""Database related class and methods"""

from typing import Dict, List, Optional, Union

import psycopg2
import streamlit as st
import pandas as pd
from sqlalchemy.sql import text


class Database:
    """Manages database functionality"""

    # db_name: str
    # db_user: str
    # db_password: str
    # db_host: str
    # db_port: int
    # connection: SQLConnection

    def __init__(self):
        """Initialize the database connection."""
        try:
            self.connection = st.connection(name="postgresql", type="sql")
            print(f"Connection to {st.secrets.connections.postgresql.host} successful")
        except psycopg2.OperationalError as e:
            print(f"Database Error: '{e}'")

    # @st.cache_resource
    # def _create_connection(self) -> psycopg2.extensions.connection:
    #     """Create and caches the connection with the database."""
    #     return psycopg2.connect(
    #         database=self.db_name,
    #         user=self.db_user,
    #         password=self.db_password,
    #         host=self.db_host,
    #         port=self.db_port,
    #     )

    @staticmethod
    @st.cache_resource
    def get_instance():
        """Get a Database instance

        Returns:
            Database: database instance
        """
        if "db_instance" not in st.session_state:
            st.session_state["db_connection"] = Database()
            st.rerun()
        return st.session_state["db_connection"]

    def fetch_users(self) -> pd.DataFrame:
        """Fetch all users data

        Returns:
            List[Dict]: users data
        """
        query = "SELECT * FROM users;"
        users = self.connection.query(query)
        return users

    def read_user(self, email: str) -> pd.DataFrame:
        """Check if a user exists in the database

        Args:
            email (str): user's email

        Returns:
            Optional[Tuple[int, str, str]]: user_id, username and password
        """
        query = "SELECT id, username, senha FROM users WHERE email = :email;"
        user = self.connection.query(query, params={"email": email})
        return user

    def create_user(self, username: str, email: str, password: str) -> pd.DataFrame:
        """Create user in the database

        Args:
            username (str): user's name
            email (str): user's email
            password (str): user's password

        Returns:
            int: user id
        """
        insert_query = "INSERT INTO users (username, email, senha) VALUES (:username, :email, :senha);"
        select_query = "SELECT id FROM users WHERE email = :email;"
        with self.connection.session as cursor:
            cursor.execute(text(insert_query), {"username": username, "email": email, "senha": password})
            cursor.commit()
            print(f"{username} registered")
        user = self.connection.query(select_query, params={"email": email})
        return user

    def create_professors(self, teachers: Optional[Dict[str, List[str]]], user_id: Union[str, int]) -> pd.DataFrame:
        """Create professors in the database

        Args:
            teachers (List[Dict[str, List[str]]]): professors's infos
            user_id (Union[str, int]): user id

        Returns:
            pd.DataFrame: return user's professors
        """

        professors_query = """INSERT INTO docentes (user_id, nome, areas_de_atuacao)
        SELECT :user_id, :nome, :especialidade WHERE NOT EXISTS (
        SELECT user_id, nome, areas_de_atuacao FROM docentes WHERE
        user_id = :user_id AND nome = :nome AND areas_de_atuacao = :especialidade
        );
        """
        user_query = """UPDATE users SET professores =
        (SELECT ARRAY(
            SELECT professor_id FROM docentes
            WHERE docentes.user_id = :user_id)
        )"""
        return_professors_query = """SELECT professor_id, nome, areas_de_atuacao FROM docentes WHERE
        docentes.user_id = :user_id;
        """
        if teachers:
            teachers_to_insert = [
                {"user_id": int(user_id), "nome": teacher, "especialidade": specialities}
                for teacher, specialities in teachers.items()
            ]
        with self.connection.session as cursor:
            cursor.execute(text(professors_query), teachers_to_insert)
            cursor.commit()
            cursor.execute(text(user_query), {"user_id": int(user_id)})
            cursor.commit()
        professors = self.connection.query(return_professors_query, params={"user_id": user_id})
        print(f"Teachers for {user_id} created")
        return professors

    def read_professor(self, user_id: Union[str, int]) -> Optional[pd.DataFrame]:
        """Read professor in the database

        Args:
            user_id (Union[str, int]): user id

        Returns:
            Optional[Tuple[int, str, List[str]]]: Tuple containing the professor's ID,
            name and specialities, None if there's no professor.
        """
        query = """
        SELECT professor_id, nome, areas_de_atuacao FROM docentes WHERE user_id = :user_id;
        """
        professor = self.connection.query(query, params={"user_id": user_id})
        if not professor.empty:
            return professor
        return None

    def delete_professor(self, professor_id: Union[str, int]) -> bool:
        """Delete professor in the database

        Args:
            professor_id (Union[str, int]): professor id

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        query = "DELETE FROM docentes WHERE professor_id = :professor_id;"
        with self.connection.session as cursor:
            cursor.execute(text(query), {"professor_id": professor_id})
            cursor.commit()
            return True
