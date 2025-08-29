import glob
import os
from flask import jsonify
from app.common_route import login_required, log_request
from celery.result import AsyncResult
from app.tasks import celery
from flask import Blueprint

status_bp = Blueprint("status", __name__)

@status_bp.route('/status/<id>', methods=["GET"])
@login_required
@log_request
def get_status(id: str):
    result = AsyncResult(id, app=celery)

    if result.state == "PENDING":
        return jsonify({"status": "pending"}), 202

    if result.state == "PROGRESS":
        return jsonify({
            "status": "downloading",
            "progress": result.info
        }), 206

    if result.state == "FAILURE":
        return jsonify({
            "status": "failed",
            "error": str(result.info)
        }), 500

    if result.state == "SUCCESS":
        matches = [os.path.basename(path) for path in glob.glob(f'/app/storage/{id}*')]
        if not matches:
            return jsonify({"status": "completed_but_missing_file"}), 500
        return jsonify({
            "status": "completed",
            "result": result.info
        }), 200
    
    return jsonify({"status": "Unknown"}), 500