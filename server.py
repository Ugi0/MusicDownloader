from flask import Flask, Response, stream_with_context, request, send_file, make_response
from waitress import serve
import yt_dlp
import os
import json
import taglib
import shutil
import logging
import base64
from dotenv import load_dotenv
import rsa

import logging
logging.basicConfig(filename='/app/storage/out.log', level=logging.NOTSET,
    format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger=logging.getLogger(__name__)

def load_keys():
    public_key_path = '/run/secrets/public_key'
    private_key_path = '/run/secrets/private_key'
    secret_key_path = '/run/secrets/secret_key'
    with open(secret_key_path, "r") as f:
        secret_key = f.read().splitlines()[0]
    with open(public_key_path, "r") as f:
        public = f.read()
    with open(private_key_path, "rb") as f:
        private = rsa.PrivateKey.load_pkcs1(f.read())
    return private, public, secret_key

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

private, public, secret = load_keys()

app = Flask(__name__)

@app.route('/key')
def get_key():
    response = make_response(public, 200)
    response.mimetype = "text/plain"
    return response

@app.route('/', methods=["POST"])
def main():
    try:
        data = rsa.decrypt(base64.b64decode(request.data), private)
    except Exception as e:
        return "Not encoded correctly", 400
    jdata = json.loads(data)
    if jdata["secret"] != secret:
        return "Not allowed", 401
    name = jdata['title']
    url = jdata['url']
    yt_opts = {
            'outtmpl' : f'/tmp/{name}.%(ext)s',
            'extract_audio' : True,
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }]
        }
    #Download song
    new, filename = get_filename_func(f'/app/storage/{name}.wav', jdata['author'])
    print(new, filename)
    if new:
        try:
            with yt_dlp.YoutubeDL(yt_opts) as ydl:
                ydl.download(url)
        except Exception as e:
            logger.error(e)
            return f"Error while downloading: {e}", 503
        with taglib.File(f'/tmp/{name}.wav', save_on_exit=True) as song:
            song.tags["ARTIST"] = jdata["author"]
        shutil.copy2(f'/tmp/{name}.wav', f'/app/storage/{filename}')
    response = make_response(send_file(f'/app/storage/{filename}', filename))
    response.headers['filename'] = filename
    return response

if __name__ == "__main__":
    serve(app, host='0.0.0.0', port=8123)
