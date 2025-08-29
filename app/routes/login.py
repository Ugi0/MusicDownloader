from datetime import datetime, timezone, timedelta
from flask import request, jsonify
import jwt
import os
from app.common_route import engine, log_request
import bcrypt
from app.queries import get_hashed_password_query
from flask import Blueprint

login_bp = Blueprint("login", __name__)

JWT_SECRET = os.getenv("JWT_SECRET") or os.getenv("SECRET_KEY") or "default_jwt_secret"
JWT_ALGORITHM = "HS256"
JWT_TOKEN_DURATION = 3600

@login_bp.route('/login', methods=["POST"])
@log_request
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']

    with engine.begin() as conn:
        result = conn.execute(get_hashed_password_query(), {"username": username})
        row = result.mappings().fetchone()
    if row and check_password(password, row["password_hash"].encode('utf-8')):
        payload = {
            "sub": username,
            "exp": datetime.now(timezone.utc) + timedelta(seconds=JWT_TOKEN_DURATION)
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        if isinstance(token, bytes):
            token = token.decode('utf-8')
        return jsonify({"token": token}), 200
    else:
        return "Invalid credentials", 401
    
def check_password(plain_password: str, hashed_password: bytes) -> bool:
    password_bytes = plain_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_password)