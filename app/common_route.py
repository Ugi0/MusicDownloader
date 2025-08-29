from flask import request, jsonify
import os
from sqlalchemy import create_engine
from functools import wraps
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
import logging
from typing import Callable, TypeVar, Any, cast

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

secret = os.getenv("SECRET_KEY")
db_url = os.getenv("DATABASE_URL", "")

JWT_SECRET = os.getenv("JWT_SECRET") or os.getenv("SECRET_KEY") or "default_jwt_secret"
JWT_ALGORITHM = "HS256"

if not db_url:
    raise ValueError("DATABASE_URL environment variable is not set")
engine = create_engine(db_url)

F = TypeVar('F', bound=Callable[..., Any])

def log_request(f: F) -> F:
    @wraps(f)
    def decorated_function(*args: object, **kwargs: object) -> object:
        logger.info(f'{request.method} request to {request.path}')
        ret = f(*args, **kwargs)
        logger.info(f'Response: {ret}')
        return ret
    return cast(F, decorated_function)

def login_required(f: F) -> F:
    @wraps(f)
    def decorated_function(*args: object, **kwargs: object) -> object:
        auth_header = request.headers.get("Authorization", None)
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid token"}), 401

        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        return f(*args, **kwargs)
    return cast(F, decorated_function)
