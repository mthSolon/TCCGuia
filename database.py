import psycopg2
import psycopg2.extras
import streamlit as st
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class Database:
    """Manages database functionality"""
    db_name: str
    db_user: str
    db_password: str
    db_host: str
    db_port: int

    def init_connection(self):
        """Initialize the database connection."""
        try:
            self.connection = self._create_connection()
        except psycopg2.OperationalError as e:
            print(f"Error: '{e}'")
    
    @st.cache_resource
    def _create_connection(self) -> psycopg2.extensions.connection:
        """Create and caches the connection with the database."""
        print(f"Connection to {st.secrets.db_credentials.db_host} successful")
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
        users = None
        with self.connection.cursor() as cursor:
            try:
                cursor.execute(query)
                users = cursor.fetchall()
                return users
            except psycopg2.OperationalError as e:
                print(f"Error: '{e}'")
    
    def check_user(self, email: str) -> Optional[str]:
        """Check if a user exists in the database

        Args:
            email (str): user's email

        Returns:
            Optional[str]: user name
        """
        query = f"SELECT username, senha FROM users WHERE email = %s;"
        user = None
        with self.connection.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor) as cursor:
            try:
                cursor.execute(query, (email,))
                user = cursor.fetchone()
                if user:
                    return user.username, user.senha
                return None
            except psycopg2.Error as e:
                print(f"Error: {e}")

    def insert_user(self, username: str, email: str, password: str) -> bool:
        """Insert user in the database

        Args:
            username (str): user's name
            email (str): user's email
            password (str): user's password

        Returns:
            bool: True if operation was sucessful, False otherwise.
        """
        query = f"INSERT INTO users (username, email, senha) VALUES (%s, %s, %s);"
        with self.connection.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor) as cursor:
            try:
                self.connection.autocommit = False
                cursor.execute("BEGIN;")
                cursor.execute(query, (username, email, password))
                self.connection.commit()
                print(f"{username} registered")
                return True
            except psycopg2.Error as e:
                self.connection.rollback()
                print(f"Error: {e}")
                return False