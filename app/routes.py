from flask import Blueprint, request, send_file, current_app
from .tasks import start_download_task
import hmac
import os
import bcrypt
from sqlalchemy import text, create_engine
from app.queries import *;

app = Blueprint("main", __name__)

secret = os.getenv("SECRET_KEY")
db_url = os.getenv("DATABASE_URL", "")

if not db_url:
    raise ValueError("DATABASE_URL environment variable is not set")
engine = create_engine(db_url)

@app.before_request
def log_request():
    current_app.logger.info(f'{request.method} request to {request.path}')

@app.route('/login', methods=["POST"])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']

    with engine.begin() as conn:
        stored_hash = conn.execute(get_hashed_password_query(), {"username": username})

    if stored_hash and check_password(password, stored_hash.encode('utf-8')):
        return "Login successful", 200
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
def get_status(id: str):
    if os.path.exists(f'/app/storage/{id}'):
        return "File exists", 200
    else:
        return "File does not exist", 404
    
@app.route('/delete/<id>')
def delete_file(id: str):
    if os.path.exists(f'/app/storage/{id}'):
        os.remove(f'/app/storage/{id}')
        return "File deleted", 200
    else:
        return "File does not exist", 404
    
@app.route('/download/<id>')
def download_file(id: str):
    if os.path.exists(f'/app/storage/{id}'):
        return send_file(f'/app/storage/{id}', as_attachment=True)
    else:
        return "File does not exist", 404

@app.route('/', methods=["GET"])
def root_get():
    return "Not allowed", 418

@app.route('/start_download', methods=["POST"])
def start_post():
    data = request.get_json()
    user_secret = data.get("secret", "")

    if not hmac.compare_digest(user_secret, secret):
        return "Unauthorized", 401

    url = data.get("url")
    title = data.get("title")
    author = data.get("author", "")

    if not url or not title:
        return "Missing parameters", 400

    start_download_task.delay(url, title, author)
    return "Download started", 200

def hash_password(plain_password: str) -> str:
    password_bytes = plain_password.encode('utf-8')
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode('utf-8')

def check_password(plain_password: str, hashed_password: bytes) -> bool:
    password_bytes = plain_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_password)
