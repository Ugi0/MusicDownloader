from . import celery
from app.downloader import download_file

@celery.task
def start_download_task(url: str, title: str, author: str, format: str = 'mp3'):
    download_file(url, title, author, format)
