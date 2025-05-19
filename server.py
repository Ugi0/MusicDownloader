from flask import Flask, Response, stream_with_context, request, send_file, make_response
from waitress import serve
import yt_dlp
import logging
import os
import json
import taglib
import shutil
import base64
from dotenv import load_dotenv
import rsa

#logging.basicConfig()
#logger = logging.getLogger('waitress')
#logger.setLevel(logging.DEBUG)

app = Flask(__name__)

@app.before_request
def log_request_info():
    print(f'{request.method} request to {request.path}')
    return None

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

@app.route('/key')
def get_key():
    response = make_response(public, 200)
    response.mimetype = "text/plain"
    return response

@app.route('/', methods=["GET"])
def root_get():
    return "Not allowed", 418

@app.route('/', methods=["POST"])
def root_post():
    if request.data == "":
        return "Not allowed", 418
    try:
        data = rsa.decrypt(base64.b64decode(request.data), private)
    except Exception as e:
        print(f"Not encoded correctly: {e}")
        return "Not allowed", 400
    print(data)
    jdata = json.loads(data)
    if jdata["secret"] != secret:
        print("Not allowed")
        return "Not allowed", 401
    name = jdata['title']
    url = jdata['url']
    yt_opts = {
            'outtmpl' : f'/tmp/{name}.%(ext)s',
            'extract_audio' : True,
            'format': 'bestaudio/best',
	    'cookiefile': 'cookiefile',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }]
        }
    #Download song
    new, filename = get_filename_func(f'/app/storage/{name}.wav', jdata['author'])
    print(f'{new}, {filename}')
    if new:
        try:
            with yt_dlp.YoutubeDL(yt_opts) as ydl:
                ydl.download(url)
        except Exception as e:
            print(f"Error while downloading: {e}")
            return f"Error while downloading: {e}", 503
        with taglib.File(f'/tmp/{name}.wav', save_on_exit=True) as song:
            song.tags["ARTIST"] = jdata["author"]
        shutil.copy2(f'/tmp/{name}.wav', f'/app/storage/{filename}')
    response = make_response(send_file(f'/app/storage/{filename}', filename))
    response.headers['filename'] = filename
    return response

if __name__ == "__main__":
    serve(app, host='0.0.0.0', port=80)
