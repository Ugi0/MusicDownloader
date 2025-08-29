import hmac
from flask import request
from app.common_route import engine, log_request, secret
import bcrypt
from app.queries import insert_user_query
from flask import Blueprint

register_bp = Blueprint("register", __name__)

@register_bp.route('/register', methods=["POST"])
@log_request
def register():
    data = request.get_json()
    userSecret = data.get('secret') if data else None

    if not hmac.compare_digest(str(userSecret or ""), str(secret or "")):
        return "Not allowed", 401

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return "Missing parameters", 400

    hashed = hash_password(password)

    with engine.begin() as conn:
        conn.execute(insert_user_query(), {"username": username, "password": hashed})
    return "Success", 200

def hash_password(plain_password: str) -> str:
    password_bytes = plain_password.encode('utf-8')
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode('utf-8')