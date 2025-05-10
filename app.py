from flask import Flask, request, jsonify
from yt_dlp import YoutubeDL
import os, requests, time
from datetime import datetime

app = Flask(__name__)

@app.route('/getmp3')
def get_mp3():
    query = request.args.get('query')
    if not query:
        return jsonify({'error': 'Missing "query" parameter'}), 400

    yt_url = query if query.startswith("http") else f"ytsearch:{query}"
    base_name = 'audio'

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': base_name,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(yt_url, download=False)
            if 'entries' in info:
                info = info['entries'][0]

            title = info.get('title', 'Unknown Title')
            uploader = info.get('uploader', 'Unknown Uploader')
            duration = time.strftime('%H:%M:%S', time.gmtime(info.get('duration', 0)))
            video_url = info.get('webpage_url')

            # Download the audio
            ydl.download([yt_url])

        # Upload to Catbox
        mp3_filename = f"{base_name}.mp3"
        with open(mp3_filename, 'rb') as f:
            files = {'fileToUpload': (os.path.basename(mp3_filename), f)}
            data = {'reqtype': 'fileupload'}
            res = requests.post('https://catbox.moe/user/api.php', data=data, files=files)

        if res.status_code == 200 and res.text.startswith("https"):
            catbox_url = res.text.strip()
            os.remove(mp3_filename)
            return jsonify({
                'title': title,
                'uploader': uploader,
                'duration': duration,
                'video_url': video_url,
                'mp3_url': catbox_url.replace("https", "http")
            })
        else:
            return jsonify({'error': 'Failed to upload to Catbox'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
