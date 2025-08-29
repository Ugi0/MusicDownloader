from app.common_route import log_request
from flask import Blueprint

root_bp = Blueprint("root", __name__)

@root_bp.route('/', methods=["GET"])
@log_request
def root_get():
    return "Not allowed", 418