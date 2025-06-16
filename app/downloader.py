import yt_dlp
import shutil
import taglib

def download_file(id: str, title: str, author: str, format: str):
    yt_opts = {
            'outtmpl' : f'/tmp/{id}',
            'extract_audio' : True,
            'format': 'bestaudio/best',
            'cookiefile': 'cookiefile',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': format,
            }]
        }
    #Download song
    try:
        with yt_dlp.YoutubeDL(yt_opts) as ydl:
            ydl.download(id)
        with taglib.File(f'/tmp/{title}.wav', save_on_exit=True) as song:
            song.tags["ARTIST"] = author
            song.tags["TITLE"] = title
            song.tags["FORMAT"] = format
            shutil.copy2(f'/tmp/{id}', f'/app/storage/{id}')
    except Exception as e:
        print(f"Error while downloading: {e}")
        return f"Error while downloading: {e}", 503