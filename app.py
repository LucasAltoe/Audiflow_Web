from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from pathlib import Path
from yt_dlp import YoutubeDL
import pygame
import os
import json
import threading
from plyer import notification
import logging

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

music_files = []
playlist = []
current_index = 0
paused = False
equalizer_settings = [0] * 10
play_history = []

pygame.init()
pygame.mixer.init()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

@app.route('/')
def index():
    app.logger.debug("Rendering index page")
    return render_template('index.html')

@app.route('/choose_folder', methods=['POST'])
def choose_folder():
    files = request.json.get('files')
    app.logger.debug(f"Files received: {files}")
    global music_files, playlist, current_index
    music_files = [str(Path(file)) for file in files if file.endswith(('.mp3', '.wav', '.flac', '.ogg'))]
    app.logger.debug(f"Music files found: {music_files}")
    if music_files:
        current_index = 0
        playlist = music_files.copy()
        play_music()
    return jsonify({'playlist': playlist})

@app.route('/create_playlist', methods=['POST'])
def create_playlist():
    files_selected = request.json.get('files')
    app.logger.debug(f"Files selected for playlist: {files_selected}")
    global playlist, current_index
    if files_selected:
        playlist = list(files_selected)
        current_index = 0
        play_music()
    return jsonify({'playlist': playlist})

@app.route('/add_from_youtube', methods=['POST'])
def add_from_youtube():
    youtube_url = request.json.get('url')
    app.logger.debug(f"YouTube URL received: {youtube_url}")
    threading.Thread(target=download_youtube_audio, args=(youtube_url,)).start()
    return jsonify({'status': 'downloading'})

def download_youtube_audio(youtube_url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'noplaylist': True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
            info_dict = ydl.extract_info(youtube_url, download=False)
            title = info_dict.get('title', None)
            file_name = ydl.prepare_filename(info_dict).replace('.webm', '.mp3').replace('.m4a', '.mp3')
            playlist.append(file_name)
            app.logger.debug(f"Downloaded and added to playlist: {file_name}")
            show_notification("Download Concluído", title)
            app.logger.debug(f"Emitting new_music event for {file_name}")
            with app.app_context():
                socketio.emit('new_music', {'title': title, 'file_name': file_name})
    except Exception as e:
        app.logger.error(f"Erro ao baixar áudio do YouTube: {e}")

def play_music():
    global paused
    if playlist:
        file_path = Path(playlist[current_index]).resolve()
        app.logger.debug(f"Tentando reproduzir: {file_path}")

        if file_path.exists():
            if not pygame.mixer.get_init():
                pygame.mixer.init()

            try:
                pygame.mixer.music.load(str(file_path))
                pygame.mixer.music.set_volume(0.5)
                pygame.mixer.music.play()
                paused = False
                show_notification("Reproduzindo", os.path.basename(file_path))
                add_to_history(file_path)
                app.logger.debug(f"Reproduzindo: {file_path}")
            except pygame.error as e:
                app.logger.error(f"Erro ao carregar arquivo de música: {e}")
        else:
            app.logger.error(f"Erro: O arquivo não existe - {file_path}")

@app.route('/play_pause', methods=['POST'])
def play_pause():
    global paused
    if playlist:
        if not pygame.mixer.music.get_busy() or paused:
            pygame.mixer.music.unpause()
            paused = False
            show_notification("Reproduzindo", os.path.basename(playlist[current_index]))
        else:
            pygame.mixer.music.pause()
            paused = True
            show_notification("Pausado", os.path.basename(playlist[current_index]))
    return jsonify({'status': 'playing' if not paused else 'paused'})

@app.route('/play_next', methods=['POST'])
def play_next():
    global current_index
    if playlist:
        current_index = (current_index + 1) % len(playlist)
        play_music()
    return jsonify({'status': 'next'})

@app.route('/play_previous', methods=['POST'])
def play_previous():
    global current_index
    if playlist:
        current_index = (current_index - 1) % len(playlist)
        play_music()
    return jsonify({'status': 'previous'})

@app.route('/update_volume', methods=['POST'])
def update_volume():
    volume = request.json.get('volume')
    app.logger.debug(f"Volume updated to: {volume}")
    if playlist:
        pygame.mixer.music.set_volume(float(volume))
    return jsonify({'status': 'volume updated'})

@app.route('/save_playlist', methods=['POST'])
def save_playlist():
    playlist_name = request.json.get('name')
    app.logger.debug(f"Saving playlist as: {playlist_name}")
    if playlist_name:
        with open(f"{playlist_name}.json", 'w') as f:
            json.dump(playlist, f)
    return jsonify({'status': 'playlist saved'})

@app.route('/load_playlist', methods=['POST'])
def load_playlist():
    file_path = request.json.get('path')
    app.logger.debug(f"Loading playlist from: {file_path}")
    global playlist, current_index
    if file_path:
        with open(file_path, 'r') as f:
            playlist = json.load(f)
        current_index = 0
        play_music()
    return jsonify({'status': 'playlist loaded', 'playlist': playlist})

def add_to_history(file_path):
    play_history.append(str(file_path))
    if len(play_history) > 100:
        play_history.pop(0)

@app.route('/show_history', methods=['GET'])
def show_history():
    app.logger.debug("Showing play history")
    return jsonify({'history': play_history})

def show_notification(title, message):
    notification.notify(
        title=title,
        message=message,
        timeout=5
    )

if __name__ == '__main__':
    socketio.run(app, debug=True)
