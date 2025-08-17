import glob
import os
from flask import jsonify
from app.routes import app, login_required, log_request

@app.route('/status/<id>')
@login_required
@log_request
def get_status(id: str):
    matches = [os.path.basename(path) for path in glob.glob(f'/app/storage/{id}')]
    if not matches:
        return "File does not exist", 404
    return jsonify({"status": "exists", "files": matches}), 200