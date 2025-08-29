from tinytag import TinyTag
from flask import make_response, send_file
import os
from app.common_route import login_required, log_request
from flask import Blueprint

download_bp = Blueprint("download", __name__)

@download_bp.route('/download/<filename>', methods=["GET"])
@login_required
@log_request
def download_file(filename: str):
    path = f'/app/storage/{filename}'
    if os.path.exists(path):
        tag = TinyTag.get(path)
        response = make_response(send_file(path_or_file=path, as_attachment=True, download_name=tag.filename, mimetype=f'audio/{format}'))
        response.headers["filename"] = tag.filename or filename
        return response
    else:
        return "File does not exist", 404