from flask import Blueprint, make_response, request, send_file, current_app, jsonify
from .tasks import start_download_task
import hmac
import os
import bcrypt
from sqlalchemy import create_engine
from app.queries import *
from functools import wraps
import jwt
import taglib
import glob
import logging
from datetime import datetime, timezone, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Blueprint("main", __name__)

JWT_SECRET = os.getenv("JWT_SECRET", os.getenv("SECRET_KEY"))
JWT_ALGORITHM = "HS256"
JWT_TOKEN_DURATION = 3600

secret = os.getenv("SECRET_KEY")
db_url = os.getenv("DATABASE_URL", "")

if not db_url:
    raise ValueError("DATABASE_URL environment variable is not set")
engine = create_engine(db_url)

def log_request(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        logger.info(f'{request.method} request to {request.path}')
        ret = f(*args, **kwargs)
        logger.info(f'Response: {ret}')
        return ret
    return decorated_function

def login_required(f):
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

@app.route('/', methods=["GET"])
@log_request
def root_get():
    return "Not allowed", 418

@app.route('/login', methods=["POST"])
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
        return jsonify({"token": token}), 200
    else:
        return "Invalid credentials", 401

@app.route('/register', methods=["POST"])
@log_request
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
@log_request
def get_status(id: str):
    matches = [os.path.basename(path) for path in glob.glob(f'/app/storage/{id}.*')]
    if not matches:
        return "File does not exist", 404
    return jsonify({"status": "exists", "files": matches}), 200
    
@app.route('/delete/<filename>')
@login_required
@log_request
def delete_file(filename: str):
    if os.path.exists(f'/app/storage/{filename}'):
        os.remove(f'/app/storage/{filename}')
        return "File deleted", 200
    else:
        return "File does not exist", 404
    
@app.route('/download/<filename>')
@login_required
@log_request
def download_file(filename: str):
    if os.path.exists(f'/app/storage/{filename}'):
        logger.info("file exists")
        with taglib.File(f'/app/storage/{filename}', save_on_exit=True) as song:
            title = song.tags.get("TITLE", ["unknown"])[0]
            format = song.tags.get("FORMAT", ["mp3"])[0]
            response = make_response(send_file(path_or_file=f'/app/storage/{filename}', as_attachment=True, download_name=f'{title}.{format}', mimetype=f'audio/{format}'))
            response.headers["filename"] = f'{title}.{format}'
            return response
    else:
        return "File does not exist", 404

@app.route('/start_download', methods=["POST"])
@login_required
@log_request
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
