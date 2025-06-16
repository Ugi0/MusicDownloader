from flask import Blueprint, request, send_file, current_app, jsonify
from .tasks import start_download_task
import hmac
import os
import bcrypt
from sqlalchemy import create_engine
from app.queries import *
from functools import wraps
import jwt
import taglib
from datetime import datetime, timezone, timedelta

app = Blueprint("main", __name__)

JWT_SECRET = os.getenv("JWT_SECRET", os.getenv("SECRET_KEY"))
JWT_ALGORITHM = "HS256"
JWT_TOKEN_DURATION = 3600

secret = os.getenv("SECRET_KEY")
db_url = os.getenv("DATABASE_URL", "")

if not db_url:
    raise ValueError("DATABASE_URL environment variable is not set")
engine = create_engine(db_url)

def login_required(f: function) -> function:
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization", None)
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid token"}), 401

        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            request.user = payload["sub"]
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        return f(*args, **kwargs)
    return decorated_function

@app.before_request
def log_request():
    current_app.logger.info(f'{request.method} request to {request.path}')

@app.route('/', methods=["GET"])
def root_get():
    return "Not allowed", 418

@app.route('/login', methods=["POST"])
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
        return jsonify({"token": token}), 200
    else:
        return "Invalid credentials", 401

@app.route('/register', methods=["POST"])
def register():
    data = request.get_json()
    userSecret = data.get('secret') if data else None

    if not hmac.compare_digest(userSecret or "", secret):
        return "Not allowed", 401

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return "Missing parameters", 400

    hashed = hash_password(password)

    with engine.begin() as conn:
        conn.execute(insert_user_query(), {"username": username, "password": hashed})
    return "Success", 200

@app.route('/status/<id>')
@login_required
def get_status(id: str):
    if os.path.exists(f'/app/storage/{id}'):
        return "File exists", 200
    else:
        return "File does not exist", 404
    
@app.route('/delete/<id>')
@login_required
def delete_file(id: str):
    if os.path.exists(f'/app/storage/{id}'):
        os.remove(f'/app/storage/{id}')
        return "File deleted", 200
    else:
        return "File does not exist", 404
    
@app.route('/download/<id>')
@login_required
def download_file(id: str):
    if os.path.exists(f'/app/storage/{id}'):
        with taglib.File(f'/app/storage/{id}', save_on_exit=True) as song:
            title = song.tags.get("TITLE", ["unknown"])[0]
            format = song.tags.get("FORMAT", ["mp3"])[0]
            return send_file(path_or_file= f'/app/storage/{id}', as_attachment=True, download_name=f'{title}.{format}', mimetype=f'audio/{format}')
    else:
        return "File does not exist", 404

@app.route('/start_download', methods=["POST"])
@login_required
def start_post():
    data = request.get_json()

    id = data.get("id")
    title = data.get("title")
    author = data.get("author", "")
    format = data.get("format", "mp3")

    if not id or not title:
        return "Missing parameters", 400

    start_download_task.delay(id, title, author, format)
    return "Download started", 200

def hash_password(plain_password: str) -> str:
    password_bytes = plain_password.encode('utf-8')
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode('utf-8')

def check_password(plain_password: str, hashed_password: bytes) -> bool:
    password_bytes = plain_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_password)
