import os
from flask import request
from app.common_route import login_required, log_request
from app.settings import downloader_settings
from flask import Blueprint
from app import celery
from app.common_route import logger

start_download_bp = Blueprint("start_download", __name__)

@start_download_bp.route('/start_download', methods=["POST"])
@login_required
@log_request
def start_post():
    data = request.get_json()

    logger.info(f'Data: {data}')

    id = data.get("id")
    title = data.get("title")
    author = data.get("author", "")
    format = data.get("format", "mp3")
    trimFromStart = data.get("start", -1)
    trimFromEnd = data.get("end", -1)
    delete_cache = data.get("no_cache", False)

    if os.path.exists(f'/app/storage/{id}'):
        if delete_cache:
            os.remove(f'/app/storage/{id}')
        else:
            return "File already exists. Use 'no_cache' to overwrite.", 400

    settings = downloader_settings(id, title, author, format, trimFromStart, trimFromEnd)

    if not id or not title:
        return "Missing parameters", 400

    celery.send_task("start_download_task", task_id=settings.id, args=[settings.to_dict()])
    return "Download started", 201