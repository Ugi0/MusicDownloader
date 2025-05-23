from sqlalchemy import text

def insert_user_query() -> text:
    return text(
	"INSERT INTO users (username, password_hash) VALUES (:username, :password)"
    )

def get_hashed_password_query() -> text:
    return text(
	"SELECT password_hash FROM users WHERE username = ':username'"
    )
