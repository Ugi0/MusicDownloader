from tinytag import TinyTag
from flask import make_response, send_file
import os
from app.routes import app, login_required, log_request

@app.route('/download/<filename>')
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