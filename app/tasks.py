from celery import Celery, Task
from typing import cast
from app.downloader import download_file
from app.settings import downloader_settings

celery = Celery(__name__)

@celery.task(name="start_download_task")
def start_download_task(settings: downloader_settings) -> None:
    download_file(settings)

start_download_task = cast(Task, start_download_task)