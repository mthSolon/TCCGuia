"""Database related class and methods"""

from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
import psycopg2
from psycopg2.extras import execute_batch, NamedTupleCursor
import streamlit as st


@dataclass
class Database:
    """Manages database functionality"""

    db_name: str
    db_user: str
    db_password: str
    db_host: str
    db_port: int
    connection: psycopg2.extensions.connection = field(default=None, init=False)

    def init_connection(self):
        """Initialize the database connection."""
        try:
            self.connection = self._create_connection()
            print(f"Connection to {st.secrets.db_credentials.db_host} successful")
        except psycopg2.OperationalError as e:
            print(f"Database Error: '{e}'")

    @st.cache_resource
    def _create_connection(self) -> psycopg2.extensions.connection:
        """Create and caches the connection with the database."""
        return psycopg2.connect(
            database=self.db_name,
            user=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
        )

    def fetch_users(self) -> List[Dict]:
        """Fetch all users data

        Returns:
            List[Dict]: users data
        """
        query = "SELECT * FROM users;"
        cursor = self.connection.cursor()
        with self.connection.cursor() as cursor:
            cursor.execute(query)
            users = cursor.fetchall()
            return users

    def read_user(self, email: str) -> Optional[Tuple[int, str]]:
        """Check if a user exists in the database

        Args:
            email (str): user's email

        Returns:
            Optional[Tuple[int, str]]: user_id, username and password
        """
        query = "SELECT id, username, senha FROM users WHERE email = %s;"
        with self.connection.cursor(cursor_factory=NamedTupleCursor) as cursor:
            cursor.execute(query, (email,))
            user = cursor.fetchone()
            if user:
                return user.id, user.username, user.senha
            return None, None, None

    def create_user(self, username: str, email: str, password: str) -> int:
        """Create user in the database

        Args:
            username (str): user's name
            email (str): user's email
            password (str): user's password

        Returns:
            int: user id
        """
        insert_query = "INSERT INTO users (username, email, senha) VALUES (%s, %s, %s);"
        select_query = "SELECT id FROM users WHERE email = %s;"
        with self.connection.cursor(cursor_factory=NamedTupleCursor) as cursor:
            cursor.execute(insert_query, (username, email, password))
            self.connection.commit()
            print(f"{username} registered")
            cursor.execute(select_query, (email,))
            user = cursor.fetchone()
            return user.id

    def create_professors(
        self, teachers: List[Dict[str, List[str]]], user_id: Union[str, int]
    ) -> bool:
        """Create professors in the database

        Args:
            teachers (List[Dict[str, List[str]]]): professors's infos
            user_id (Union[str, int]): user id

        Returns:
            bool: True if operation was successful
        """

        professors_query = """INSERT INTO docentes (user_id, nome, areas_de_atuacao)
        SELECT %(user_id)s, %(nome)s, %(especialidade)s WHERE NOT EXISTS (
        SELECT user_id, nome, areas_de_atuacao FROM docentes WHERE
        user_id = %(user_id)s AND nome = %(nome)s AND areas_de_atuacao = %(especialidade)s  
        );
        """
        user_query = """UPDATE users SET professores =
        (SELECT ARRAY(
            SELECT professor_id FROM docentes
            WHERE docentes.user_id = %s)
        )"""
        teachers_to_insert = [
            {"user_id": int(user_id), "nome": teacher, "especialidade": specialties}
            for teacher, specialties in teachers.items()
        ]
        with self.connection.cursor(cursor_factory=NamedTupleCursor) as cursor:
            execute_batch(cursor, professors_query, teachers_to_insert)
            self.connection.commit()
            cursor.execute(user_query, (int(user_id),))
            self.connection.commit()
            print(f"Teachers for {user_id} created")
            return True

    def read_professor(
        self, professor_name: str, user_id: Union[str, int]
    ) -> Optional[Tuple[int, str, List[str]]]:
        """Read professor in the database

        Args:
            professor_name (str): professor's name
            user_id (Union[str, int]): user id

        Returns:
            Optional[Tuple[int, str, List[str]]]: Tuple containing the professor's ID,
            name and specialties, None if there's no professor.
        """
        query = """
        SELECT professor_id, nome, areas_de_atuacao FROM docentes WHERE user_id = %s AND nome = %s;
        """
        with self.connection.cursor(cursor_factory=NamedTupleCursor) as cursor:
            cursor.execute(query, (int(user_id), professor_name))
            professor = cursor.fetchone()
            if professor:
                return (
                    professor.professor_id,
                    professor.nome,
                    professor.areas_de_atuacao,
                )
            return None, None, None

    def delete_professor(self, professor_id: Union[str, int]) -> bool:
        """Delete professor in the database

        Args:
            professor_id (Union[str, int]): professor id

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        query = "DELETE FROM docentes WHERE professor_id = %s;"
        with self.connection.cursor(cursor_factory=NamedTupleCursor) as cursor:
            cursor.execute(query, (int(professor_id),))
            self.connection.commit()
            return True
