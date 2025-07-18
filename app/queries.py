from sqlalchemy import text
from sqlalchemy.sql.elements import TextClause

def insert_user_query() -> TextClause:
    return text(
    "INSERT INTO users (username, password_hash) VALUES (:username, :password)"
    )

def get_hashed_password_query() -> TextClause:
    return text(
    "SELECT password_hash FROM users WHERE username = :username"
    )
