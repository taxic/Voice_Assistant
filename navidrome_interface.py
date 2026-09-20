# navidrome_interface.py
"""Client for a self-hosted Navidrome music server via the Subsonic API
(Navidrome implements the standard Subsonic REST API - see
https://www.navidrome.org/docs/developers/subsonic-api/). Read-only from
this assistant's point of view: searching the library and building stream
URLs for Chromecast to play - no library management.
"""
import hashlib
import os
import random
import string

import requests
from config_manager import config

API_VERSION = "1.16.1"
CLIENT_NAME = "jarvis-voice-assistant"


class NavidromeError(Exception):
    """Raised when the Navidrome/Subsonic API itself reports an error."""
    pass


class NavidromeInterface:
    def __init__(self):
        self.is_authenticated = False
        self.base_url = None
        self.username = None
        self.password = None
        self._initialize()

    def _initialize(self):
        navidrome_config = config.get_section('navidrome')

        self.base_url = os.getenv(navidrome_config.get('url_env', 'NAVIDROME_URL'), '').rstrip('/')
        self.username = os.getenv(navidrome_config.get('username_env', 'NAVIDROME_USERNAME'))
        self.password = os.getenv(navidrome_config.get('password_env', 'NAVIDROME_PASSWORD'))
        self.timeout = navidrome_config.get('timeout_seconds', 10)

        if not self.base_url or not self.username or not self.password:
            print(
                "[WARN] Navidrome not configured. Set "
                f"{navidrome_config.get('url_env', 'NAVIDROME_URL')}, "
                f"{navidrome_config.get('username_env', 'NAVIDROME_USERNAME')} and "
                f"{navidrome_config.get('password_env', 'NAVIDROME_PASSWORD')} environment variables."
            )
            return

        self.is_authenticated = True

    def _auth_params(self) -> dict:
        """Fresh salt + token per call, per the Subsonic auth scheme -
        token = md5(password + salt). Never sends the raw password."""
        salt = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        token = hashlib.md5((self.password + salt).encode('utf-8')).hexdigest()
        return {
            "u": self.username,
            "t": token,
            "s": salt,
            "v": API_VERSION,
            "c": CLIENT_NAME,
            "f": "json",
        }

    def _request(self, endpoint: str, params: dict = None) -> dict:
        if not self.is_authenticated:
            raise NavidromeError("Navidrome is not configured.")

        url = f"{self.base_url}/rest/{endpoint}"
        all_params = self._auth_params()
        all_params.update(params or {})

        response = requests.get(url, params=all_params, timeout=self.timeout)
        response.raise_for_status()
        data = response.json().get("subsonic-response", {})

        if data.get("status") != "ok":
            error = data.get("error", {})
            raise NavidromeError(error.get("message", "Unknown Navidrome API error"))

        return data

    def stream_url(self, song_id: str) -> str:
        """Build a full, authenticated stream URL for a track - this is
        what gets handed to a Chromecast to actually play."""
        params = self._auth_params()
        params["id"] = song_id
        query = "&".join(f"{k}={requests.utils.quote(str(v))}" for k, v in params.items())
        return f"{self.base_url}/rest/stream?{query}"

    def search(self, query: str, song_count: int = 20, album_count: int = 10, artist_count: int = 5) -> dict:
        """Search songs/albums/artists matching `query`."""
        data = self._request("search3", {
            "query": query,
            "songCount": song_count,
            "albumCount": album_count,
            "artistCount": artist_count,
        })
        result = data.get("searchResult3", {})
        return {
            "songs": result.get("song", []),
            "albums": result.get("album", []),
            "artists": result.get("artist", []),
        }

    def get_album_songs(self, album_id: str) -> list:
        data = self._request("getAlbum", {"id": album_id})
        return data.get("album", {}).get("song", [])

    def get_playlists(self) -> list:
        data = self._request("getPlaylists")
        return data.get("playlists", {}).get("playlist", [])

    def get_playlist_songs(self, playlist_id: str) -> list:
        data = self._request("getPlaylist", {"id": playlist_id})
        return data.get("playlist", {}).get("entry", [])

    def get_random_songs(self, size: int = 20) -> list:
        data = self._request("getRandomSongs", {"size": size})
        return data.get("randomSongs", {}).get("song", [])
