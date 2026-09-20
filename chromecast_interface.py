# chromecast_interface.py
"""Casts Navidrome stream URLs to Google Cast devices for room-targeted
playback ("play jazz in the kitchen"). Room names are a config-level
mapping to each device's actual Cast friendly name, since "kitchen" isn't
necessarily what the device calls itself on the network.

Discovery is real mDNS scanning (a few seconds each time), so discovered
devices are cached per room for the life of the process rather than
re-scanned on every command - re-discovery only happens if a room hasn't
been seen yet, or the cached device stops responding.
"""
from config_manager import config

try:
    import pychromecast
    PYCHROMECAST_AVAILABLE = True
except ImportError:
    PYCHROMECAST_AVAILABLE = False
    print("[INFO] pychromecast not installed. Install with: pip install PyChromecast")


class ChromecastError(Exception):
    pass


class ChromecastManager:
    def __init__(self):
        cc_config = config.get_section('chromecast')
        self.room_map = cc_config.get('rooms', {})  # room name (lowercase) -> Cast friendly name
        self.default_room = cc_config.get('default_room')
        self.discovery_timeout = cc_config.get('discovery_timeout_seconds', 8)

        self._devices = {}  # room name -> pychromecast.Chromecast, cached

    def list_rooms(self) -> list:
        return list(self.room_map.keys())

    def _resolve_room(self, room: str = None) -> str:
        room = (room or self.default_room or "").lower().strip()
        if not room:
            raise ChromecastError("No room specified and no default room configured.")
        if room not in self.room_map:
            available = ", ".join(self.room_map) or "none configured"
            raise ChromecastError(f"I don't know a room called '{room}'. Available rooms: {available}.")
        return room

    def _get_device(self, room: str, force_rediscover: bool = False):
        if not PYCHROMECAST_AVAILABLE:
            raise ChromecastError("pychromecast isn't installed.")

        if not force_rediscover and room in self._devices:
            return self._devices[room]

        friendly_name = self.room_map[room]
        chromecasts, _ = pychromecast.get_listed_chromecasts(
            friendly_names=[friendly_name], discovery_timeout=self.discovery_timeout,
        )
        if not chromecasts:
            raise ChromecastError(f"Couldn't find the '{room}' speaker on the network.")

        cast = chromecasts[0]
        cast.wait(timeout=self.discovery_timeout)
        self._devices[room] = cast
        return cast

    def _with_device(self, room: str, action):
        """Run `action(cast)`, retrying once with a fresh discovery if the
        cached device connection turns out to be stale (e.g. it rebooted or
        got a new IP since it was last cached)."""
        try:
            cast = self._get_device(room)
            return action(cast)
        except ChromecastError:
            raise
        except Exception as e:
            print(f"[WARN] Cached Chromecast for '{room}' failed ({e}), rediscovering...")
            cast = self._get_device(room, force_rediscover=True)
            return action(cast)

    def play(self, room: str, media_url: str, title: str = None, content_type: str = "audio/mpeg") -> str:
        room = self._resolve_room(room)

        def _play(cast):
            mc = cast.media_controller
            mc.play_media(media_url, content_type, title=title)
            mc.block_until_active(timeout=self.discovery_timeout)
            return f"Playing{' ' + title if title else ''} in the {room}."

        return self._with_device(room, _play)

    def pause(self, room: str = None) -> str:
        room = self._resolve_room(room)
        return self._with_device(room, lambda cast: (cast.media_controller.pause(), f"Paused in the {room}.")[1])

    def resume(self, room: str = None) -> str:
        room = self._resolve_room(room)
        return self._with_device(room, lambda cast: (cast.media_controller.play(), f"Resumed in the {room}.")[1])

    def stop(self, room: str = None) -> str:
        room = self._resolve_room(room)
        return self._with_device(room, lambda cast: (cast.media_controller.stop(), f"Stopped in the {room}.")[1])

    def set_volume(self, volume_percent: int, room: str = None) -> str:
        room = self._resolve_room(room)
        level = max(0, min(100, volume_percent)) / 100.0
        return self._with_device(room, lambda cast: (cast.set_volume(level), f"Volume set to {volume_percent}% in the {room}.")[1])


chromecast_manager = ChromecastManager()
