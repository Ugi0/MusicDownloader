def insert_user_query(username: str, password: str) -> str:
    return f"""
        INSERT INTO user (username, password)
        VALUES ({username}, {password})
        RETURNING id;
    """

def get_hashed_password_from_db(username: str) -> str:
    return f"""
        SELECT password
        FROM user
        WHERE username = {username};
    """