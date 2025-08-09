import yt_dlp
import shutil
import pydub
import os

from app.settings import downloader_settings

def download_file(settings: dict) -> None | tuple[str, int]:
    final_path = None

    def progress_hook(d):
        nonlocal final_path
        if d['status'] == 'finished':
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
            ydl.download([settings["id"]])
        if final_path is None:
            raise Exception("Download failed, no final path found.")
        song = pydub.AudioSegment.from_file(f'{final_path}.{settings["format"]}')
        if settings["trimFromStart"] != "" and settings["trimFromEnd"] != "":
            song = song[parse_time_to_seconds(settings["trimFromStart"]) * 1000: -parse_time_to_seconds(settings["trimFromEnd"]) * 1000]
        elif settings["trimFromStart"] != "":
            song = song[parse_time_to_seconds(settings["trimFromStart"]) * 1000:]
        elif settings["trimFromEnd"] != "":
            song = song[:-parse_time_to_seconds(settings["trimFromEnd"]) * 1000]
        file_handle = song.export(f'{final_path}.{settings["format"]}', format=settings["format"], tags={
            'filename': f'{final_path}.{settings["format"]}'
        })
        shutil.copy2(file_handle, f'/app/storage/{settings["id"]}')
    except Exception as e:
        print(f"Error while downloading: {e}")
        return f"Error while downloading: {e}", 503

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