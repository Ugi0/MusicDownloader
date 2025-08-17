from celery import Celery, Task
from typing import cast
from app.downloader import download_file

celery = Celery(__name__)

@celery.task(name="start_download_task")
def start_download_task(settings: dict) -> None:
    download_file(settings)

start_download_task = cast(Task, start_download_task)