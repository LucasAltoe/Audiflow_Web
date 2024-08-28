document.addEventListener('DOMContentLoaded', () => {
    const chooseFolderButton = document.getElementById('choose-folder-button');
    const chooseFolderInput = document.getElementById('choose-folder');
    const createPlaylistButton = document.getElementById('create-playlist');
    const addFromYouTubeButton = document.getElementById('add-from-youtube');
    const savePlaylistButton = document.getElementById('save-playlist');
    const loadPlaylistButton = document.getElementById('load-playlist');
    const showHistoryButton = document.getElementById('show-history');
    const playPauseButton = document.getElementById('play-pause');
    const nextButton = document.getElementById('next');
    const previousButton = document.getElementById('previous');
    const volumeControl = document.getElementById('volume');
    const playlistElement = document.getElementById('playlist');
    const currentMusicInfo = document.getElementById('current-music-info');

    const socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

    chooseFolderButton.addEventListener('click', () => {
        chooseFolderInput.click();
    });

    chooseFolderInput.addEventListener('change', (event) => {
        const files = Array.from(event.target.files);
        const filePaths = files.map(file => file.webkitRelativePath);

        fetch('/choose_folder', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ files: filePaths }),
        })
        .then(response => response.json())
        .then(data => {
            console.log('Playlist:', data.playlist);
            updatePlaylist(data.playlist);
        })
        .catch(error => console.error('Erro:', error));
    });

    createPlaylistButton.addEventListener('click', () => {
        const files = prompt('Digite os caminhos dos arquivos de música separados por vírgula:').split(',');
        if (files) {
            fetch('/create_playlist', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ files }),
            })
            .then(response => response.json())
            .then(data => {
                console.log('Playlist:', data.playlist);
                updatePlaylist(data.playlist);
            })
            .catch(error => console.error('Erro:', error));
        }
    });

    addFromYouTubeButton.addEventListener('click', () => {
        const url = prompt('Digite a URL do vídeo do YouTube:');
        if (url) {
            fetch('/add_from_youtube', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url }),
            })
            .then(response => response.json())
            .then(data => console.log('Baixando áudio do YouTube:', data))
            .catch(error => console.error('Erro:', error));
        }
    });

    savePlaylistButton.addEventListener('click', () => {
        const name = prompt('Digite o nome da playlist:');
        if (name) {
            fetch('/save_playlist', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name }),
            })
            .then(response => response.json())
            .then(data => console.log('Playlist salva:', data))
            .catch(error => console.error('Erro:', error));
        }
    });

    loadPlaylistButton.addEventListener('click', () => {
        const path = prompt('Digite o caminho da playlist (arquivo JSON):');
        if (path) {
            fetch('/load_playlist', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ path }),
            })
            .then(response => response.json())
            .then(data => {
                console.log('Playlist:', data.playlist);
                updatePlaylist(data.playlist);
            })
            .catch(error => console.error('Erro:', error));
        }
    });

    showHistoryButton.addEventListener('click', () => {
        fetch('/show_history')
        .then(response => response.json())
        .then(data => {
            console.log('Histórico de reprodução:', data.history);
            alert('Histórico de reprodução:\n' + data.history.join('\n'));
        })
        .catch(error => console.error('Erro:', error));
    });

    playPauseButton.addEventListener('click', () => {
        fetch('/play_pause', {
            method: 'POST',
        })
        .then(response => response.json())
        .then(data => console.log('Reproduzindo/Pausado:', data))
        .catch(error => console.error('Erro:', error));
    });

    nextButton.addEventListener('click', () => {
        fetch('/play_next', {
            method: 'POST',
        })
        .then(response => response.json())
        .then(data => console.log('Próxima música:', data))
        .catch(error => console.error('Erro:', error));
    });

    previousButton.addEventListener('click', () => {
        fetch('/play_previous', {
            method: 'POST',
        })
        .then(response => response.json())
        .then(data => console.log('Música anterior:', data))
        .catch(error => console.error('Erro:', error));
    });

    volumeControl.addEventListener('input', () => {
        fetch('/update_volume', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ volume: volumeControl.value }),
        })
        .then(response => response.json())
        .then(data => console.log('Volume atualizado:', data))
        .catch(error => console.error('Erro:', error));
    });

    socket.on('new_music', (data) => {
        console.log('Nova música adicionada:', data);
        const li = document.createElement('li');
        li.textContent = data.file_name;
        playlistElement.appendChild(li);
    });

    function updatePlaylist(playlist) {
        playlistElement.innerHTML = '';
        playlist.forEach(song => {
            const li = document.createElement('li');
            li.textContent = song;
            playlistElement.appendChild(li);
        });
    }
});
