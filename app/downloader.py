import yt_dlp
import shutil
import taglib

def download_file(id: str, title: str, author: str, format: str):
    final_path = None

    def progress_hook(d):
        nonlocal final_path
        if d['status'] == 'finished':
            final_path = d['filename']
    
    yt_opts = {
            'outtmpl' : f'/tmp/{id}',
            'extract_audio' : True,
            'format': 'bestaudio/best',
            'cookiefile': 'cookiefile',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': format,
            }],
            'progress_hooks': [progress_hook]
        }
    #Download song
    try:
        with yt_dlp.YoutubeDL(yt_opts) as ydl:
            ydl.download([id])
        if final_path is None:
            raise Exception("Download failed, no final path found.")
        with taglib.File(f'{final_path}.{format}', save_on_exit=True) as song:
            song.tags["ARTIST"] = author
            song.tags["TITLE"] = title
            song.tags["FORMAT"] = format
        shutil.copy2(f'{final_path}.{format}', f'/app/storage/{id}')
    except Exception as e:
        print(f"Error while downloading: {e}")
        return f"Error while downloading: {e}", 503
