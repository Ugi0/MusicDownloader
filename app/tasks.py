from . import celery
from app.downloader import download_file

@celery.task
def start_download_task(id: str, title: str, author: str, format: str = 'mp3'):
    download_file(id, title, author, format)

