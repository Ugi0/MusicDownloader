import yt_dlp
import shutil
import os
import taglib

def download_file(id, title, author):
    yt_opts = {
            'outtmpl' : f'/tmp/{title}.%(ext)s',
            'extract_audio' : True,
            'format': 'bestaudio/best',
        'cookiefile': 'cookiefile',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }]
        }
    #Download song
    new, filename = get_filename_func(f'/app/storage/{title}.wav', author)
    if new:
        try:
            with yt_dlp.YoutubeDL(yt_opts) as ydl:
                ydl.download(id)
        except Exception as e:
            print(f"Error while downloading: {e}")
            return f"Error while downloading: {e}", 503
        with taglib.File(f'/tmp/{title}.wav', save_on_exit=True) as song:
            song.tags["ARTIST"] = author
        shutil.copy2(f'/tmp/{title}.wav', f'/app/storage/{filename}')
    return filename

def get_filename_func(dst, artist):
    if os.path.exists(dst):
        f = taglib.File(dst)
        if "ARTIST" in f.tags and f.tags["ARTIST"][0] == artist:
            return [False, os.path.basename(dst)]
    if not os.path.exists(dst):
        return [True, os.path.basename(dst)]
    dst, ext = ".".join(dst.split(".")[:-1]), dst.split(".")[-1]
    return get_filename_rec(dst, artist, ext, 1)

def get_filename_rec(dst, artist, ext, num):
    path = f'{dst}({num}).{ext}'
    if os.path.exists(path):
        f = taglib.File(path)
        if "ARTIST" in f.tags and f.tags["ARTIST"][0] == artist:
            return [False, path]
        return get_filename_rec(dst, artist, ext, num+1)
    return [True, os.path.basename(path)]