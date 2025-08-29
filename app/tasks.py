from celery import Task
from typing import cast
import yt_dlp
import shutil
import pydub
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3
from mutagen.id3._util import ID3NoHeaderError
from app import celery
from app.common_route import logger

@celery.task(bind=True, name="start_download_task", acks_late=True)
def start_download_task(self, settings: dict) -> None | tuple[str, int]:
    final_path = None

    def progress_hook(d):
        nonlocal final_path
        if d["status"] == "downloading":
            downloaded = d.get("downloaded_bytes", 0)
            total = d.get("total_bytes", 0) or d.get("total_bytes_estimate", 0)
            percent = int(downloaded * 100 / total) if total else 0
            eta = d.get("eta")

            self.update_state(
                state="PROGRESS",
                meta={
                    "downloaded": downloaded,
                    "total": total,
                    "percent": percent,
                    "eta_seconds": eta,
                    "speed": d.get("speed"),
                },
            )
        elif d["status"] == "processing":
            self.update_state(state="PROGRESS", meta={"stage": "conversion", "info": d})
        elif d["status"] == "finished":
            self.update_state(
                state="PROGRESS",
                meta={"status": "finished", "filename": d.get("filename")},
            )
            final_path = d['filename']
    
    yt_opts = {
            'outtmpl' : f'/tmp/{settings["id"]}',
            'extract_audio' : True,
            'format': 'bestaudio/best',
            'cookiefile': 'cookiefile',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': settings["format"],
            }],
            'progress_hooks': [progress_hook]
        }
    #Download song
    try:
        with yt_dlp.YoutubeDL(yt_opts) as ydl:
            info = ydl.extract_info(settings["id"], download=False)
            duration = 0
            if (info is not None) and ("duration" in info):
                duration = info.get("duration")
            self.update_state(
                state="PROGRESS",
                meta={
                    "duration": duration,
                },
            )
            ydl.download([settings["id"]])
        final_file = f"{final_path}.{settings['format']}"
        if settings["trimFromStart"] != "" or settings["trimFromEnd"] != "":
            song = pydub.AudioSegment.from_file(final_file)
            if settings["trimFromStart"] != "" and settings["trimFromEnd"] != "":
                song = song[parse_time_to_seconds(settings["trimFromStart"]) * 1000: parse_time_to_seconds(settings["trimFromEnd"]) * 1000]
            elif settings["trimFromStart"] != "":
                song = song[parse_time_to_seconds(settings["trimFromStart"]) * 1000:]
            elif settings["trimFromEnd"] != "":
                song = song[:parse_time_to_seconds(settings["trimFromEnd"]) * 1000]
            song.export(final_file, format=settings["format"], tags={
                'filename': final_file
            })
        try:
            e = EasyID3(final_file)
        except ID3NoHeaderError:
            ID3().save(final_file)
            e = EasyID3(final_file)

        e["artist"] = settings["author"]
        e["title"] = settings["title"]
        e.save(v2_version=3)

        shutil.copy2(final_file, f'/app/storage/{settings["id"]}')
    except Exception as e:
        raise e

start_download_task = cast(Task, start_download_task)

def parse_time_to_seconds(time_str: str) -> int:
    parts = list(map(int, time_str.split(':')))
    if len(parts) == 2:
        minutes, seconds = parts
        return minutes * 60 + seconds
    elif len(parts) == 3:
        hours, minutes, seconds = parts
        return hours * 3600 + minutes * 60 + seconds
    else:
        raise ValueError("Invalid time format")