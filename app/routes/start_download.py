import os
from flask import request
from app.tasks import start_download_task
from app.routes import app, login_required, log_request
from app.settings import downloader_settings

@app.route('/start_download', methods=["POST"])
@login_required
@log_request
def start_post():
    data = request.get_json()

    id = data.get("id")
    title = data.get("title")
    author = data.get("author", "")
    format = data.get("format", "mp3")
    trimFromStart = data.get("start", "")
    trimFromEnd = data.get("end", "")
    delete_cache = data.get("no_cache", False)

    if os.path.exists(f'/app/storage/{id}'):
        if delete_cache:
            os.remove(f'/app/storage/{id}')
        else:
            return "File already exists. Use 'no_cache' to overwrite.", 400

    settings = downloader_settings(id, title, author, format, trimFromStart, trimFromEnd)

    if not id or not title:
        return "Missing parameters", 400

    start_download_task.delay(settings.to_dict()) # type: ignore
    return "Download started", 200