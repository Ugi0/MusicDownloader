import os
from app.common_route import login_required, log_request
from flask import Blueprint

delete_bp = Blueprint("delete", __name__)

@delete_bp.route('/delete/<filename>', methods=["DELETE"])
@login_required
@log_request
def delete_file(filename: str):
    if os.path.exists(f'/app/storage/{filename}'):
        os.remove(f'/app/storage/{filename}')
        return "File deleted", 200
    else:
        return "File does not exist", 404