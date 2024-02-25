import bcrypt

class Hasher:
    
    @staticmethod
    def hash_pw(password: str) -> str:
        """Hash the password

        Args:
            password (str): user's password

        Returns:
            str: hashed password
        """
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    @staticmethod
    def check_pw(hashed_pw: str, input_pw: str) -> bool:
        """Check if the passwords match

        Args:
            hashed_pw (str): hashed password in the database
            input_pw (str): user's password input

        Returns:
            bool: True if passwords match, False otherwise
        """
        return bcrypt.checkpw(input_pw.encode(), hashed_pw.encode())