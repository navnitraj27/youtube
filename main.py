from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp
import os
import shutil
from pathlib import Path
import uuid

app = Flask(__name__)

# Configuration
DOWNLOAD_FOLDER = Path("downloads")
DOWNLOAD_FOLDER.mkdir(exist_ok=True)

def find_ffmpeg():
    """Return full path to ffmpeg executable if found in PATH, else None."""
    return shutil.which("ffmpeg")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    try:
        data = request.json
        url = data.get('url', '').strip()
        resolution = data.get('resolution', '720')
        download_type = data.get('type', 'video')
        is_playlist = data.get('playlist', False)
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Create unique folder for this download
        download_id = str(uuid.uuid4())
        output_dir = DOWNLOAD_FOLDER / download_id
        output_dir.mkdir(exist_ok=True)
        
        ffmpeg_path = find_ffmpeg()
        
        # Base options
        ydl_opts = {
            "outtmpl": str(output_dir / "%(title)s.%(ext)s"),
            "ignoreerrors": False,
        }
        
        if is_playlist:
            ydl_opts["outtmpl"] = str(output_dir / "%(playlist_title)s" / "%(title)s.%(ext)s")
        
        # Configure based on type
        if download_type == 'video':
            if ffmpeg_path:
                ydl_opts.update({
                    "format": f"bestvideo[height<={resolution}]+bestaudio/best[height<={resolution}]",
                    "merge_output_format": "mp4",
                    "ffmpeg_location": os.path.dirname(ffmpeg_path),
                })
            else:
                ydl_opts["format"] = f"best[height<={resolution}]/best"
        
        elif download_type == 'audio':
            if not ffmpeg_path:
                return jsonify({'error': 'ffmpeg is required for MP3 conversion'}), 400
            
            ydl_opts.update({
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
                "ffmpeg_location": os.path.dirname(ffmpeg_path),
            })
        
        # Download
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # Get the downloaded file
            if is_playlist:
                return jsonify({
                    'success': True,
                    'message': 'Playlist downloaded successfully',
                    'download_id': download_id
                })
            else:
                filename = ydl.prepare_filename(info)
                if download_type == 'audio':
                    filename = os.path.splitext(filename)[0] + '.mp3'
                
                return jsonify({
                    'success': True,
                    'filename': os.path.basename(filename),
                    'download_id': download_id,
                    'filepath': filename
                })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download-file/<download_id>/<filename>')
def download_file(download_id, filename):
    try:
        filepath = DOWNLOAD_FOLDER / download_id / filename
        if filepath.exists():
            return send_file(filepath, as_attachment=True)
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/cleanup', methods=['POST'])
def cleanup():
    """Clean up old download folders"""
    try:
        for folder in DOWNLOAD_FOLDER.iterdir():
            if folder.is_dir():
                shutil.rmtree(folder)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)