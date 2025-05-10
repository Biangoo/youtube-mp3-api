from flask import Flask, request, jsonify
from yt_dlp import YoutubeDL
import requests
import os
import time

app = Flask(__name__)


def get_video_info(query):
    # If not a direct YouTube URL, treat as search
    if not query.startswith("http"):
        query = f"ytsearch:{query}"

    ydl_opts = {'format': 'bestaudio/best', 'quiet': True, 'noplaylist': True, 'cookiefile': 'youtube_cookies.txt'}

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        if 'entries' in info:
            info = info['entries'][0]
        return info


def download_audio(url):
    filename = "audio"
    ydl_opts = {
        'format':
        'bestaudio/best',
        'outtmpl':
        filename,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet':
        True,
        'cookiefile': 'youtube_cookies.txt'
    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return f"{filename}.mp3"


def upload_to_catbox(file_path):
    with open(file_path, 'rb') as f:
        files = {'fileToUpload': (os.path.basename(file_path), f)}
        data = {'reqtype': 'fileupload'}
        response = requests.post('https://catbox.moe/user/api.php',
                                 data=data,
                                 files=files)
        return response.text.strip()


@app.route("/ytmp3", methods=["POST"])
def convert_to_mp3():
    try:
        data = request.get_json()
        query = data.get("query")

        info = get_video_info(query)
        title = info.get("title")
        uploader = info.get("uploader")
        duration = time.strftime('%H:%M:%S',
                                 time.gmtime(info.get("duration", 0)))
        url = info.get("webpage_url")

        mp3_file = download_audio(url)
        direct_link = upload_to_catbox(mp3_file)

        if os.path.exists(mp3_file):
            os.remove(mp3_file)

        return jsonify({
            "title": title,
            "uploader": uploader,
            "duration": duration,
            "youtube_url": url,
            "mp3_url": direct_link
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
