#!/usr/bin/env python3
"""
desktop_music_player.py - Sleek Minimal & Modern Desktop Music Player Widget for Openbox Linux
Powered by JioSaavn API & GStreamer
Features:
 - Integrated Ambient Wave at the top of the card with dynamic song palette (0.3-0.4 opacity)
 - Perfectly flush alignment from top of DesktopInputBox (761px) to bottom of ConkyGreeting (1071px)
 - Clean Square Album Art with smooth hover overlay for metadata & quick actions
 - Offline 320kbps Audio Downloader & Liked Songs / Offline Library manager
 - Interactive Track Queue & Synced Karaoke Lyrics with real-time verse highlight
"""

import os
import sys
import re
import json
import time
import math
import base64
import random
import socket
import urllib.request
import urllib.parse
import urllib.error
import threading
import subprocess
from pathlib import Path

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
gi.require_version("Gst", "1.0")
from gi.repository import Gtk, Gdk, GdkPixbuf, GdkX11, GLib, Pango, Gst

Gst.init(None)

# -----------------------------------------------------------------------------
# DIRECTORIES & OFFLINE STORAGE
# -----------------------------------------------------------------------------
MUSIC_DIR = os.path.expanduser("~/Music/JioSaavn")
CONFIG_DIR = os.path.expanduser("~/.config/jiosaavn_player")
LIKED_FILE = os.path.join(CONFIG_DIR, "liked_songs.json")
CACHE_IMG_DIR = os.path.join(CONFIG_DIR, "covers")

os.makedirs(MUSIC_DIR, exist_ok=True)
os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(CACHE_IMG_DIR, exist_ok=True)

if not os.path.exists(LIKED_FILE):
    with open(LIKED_FILE, "w") as f:
        json.dump([], f)

def get_liked_songs():
    try:
        with open(LIKED_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def save_liked_songs(songs):
    try:
        with open(LIKED_FILE, "w") as f:
            json.dump(songs, f, indent=2)
    except Exception as e:
        print(f"[MusicPlayer] Error saving liked songs: {e}")

# -----------------------------------------------------------------------------
# CSS STYLING & UNIVERSAL RESETS
# -----------------------------------------------------------------------------
CSS_DATA = """
* {
    outline: none;
}

window.desktop-music-window {
    background-color: transparent;
    background: transparent;
}

box.music-card {
    background-color: rgba(10, 10, 10, 0.96);
    border: 1px solid #262626;
    border-radius: 8px;
    padding: 8px 12px 10px 12px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.9);
}

/* Universal Button Resets */
button, button * {
    background-image: none;
    box-shadow: none;
    text-shadow: none;
    outline: none;
}

button {
    background-color: #121212;
    border: 1px solid #282828;
    border-radius: 5px;
    color: #A0A0A0;
    font-family: "JetBrainsMono Nerd Font", "JetBrains Mono", monospace;
    font-size: 9.5px;
    padding: 3px 8px;
    transition: all 120ms ease-in-out;
}

button:hover {
    background-color: #1c1c1c;
    color: #FFFFFF;
    border-color: #444444;
}

button:active {
    background-color: #080808;
    color: #50FA7B;
    border-color: #50FA7B;
}

button.btn-active {
    background-color: #16241a;
    border-color: #50FA7B;
    color: #50FA7B;
}

/* Header Elements */
label.header-title {
    color: #D4D4D4;
    font-family: "JetBrainsMono Nerd Font", "JetBrains Mono", monospace;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.5px;
}

label.status-badge {
    color: #50FA7B;
    font-family: "JetBrainsMono Nerd Font", "JetBrains Mono", monospace;
    font-size: 9px;
    font-weight: 700;
    transition: all 180ms ease-in-out;
}

label.status-badge.status-online {
    color: #50FA7B;
}

label.status-badge.status-offline {
    color: #FF5555;
}

label.status-badge.status-busy {
    color: #8BE9FD;
}

/* Action Buttons in Top Bar */
button.action-opt-btn {
    background-color: #141414;
    border: 1px solid #282828;
    border-radius: 5px;
    color: #989898;
    font-family: "JetBrainsMono Nerd Font", "JetBrains Mono", monospace;
    font-size: 9px;
    padding: 3px 7px;
}

button.action-opt-btn:hover {
    background-color: #1e1e1e;
    color: #FFFFFF;
    border-color: #404040;
}

button.action-opt-btn.btn-liked-active {
    background-color: #2b1419;
    border-color: #FF5555;
    color: #FF5555;
}

button.action-opt-btn.btn-offline-active {
    background-color: #16241a;
    border-color: #50FA7B;
    color: #50FA7B;
}

button.action-opt-btn.btn-refresh-active {
    background-color: #132433;
    border-color: #8be9fd;
    color: #8be9fd;
}

/* Search Entry */
entry.search-entry {
    background-color: #121212;
    border: 1px solid #282828;
    border-radius: 5px;
    color: #E0E0E0;
    font-family: "JetBrainsMono Nerd Font", "JetBrains Mono", monospace;
    font-size: 9.5px;
    padding: 3px 8px;
}

entry.search-entry:focus {
    border-color: #50FA7B;
    background-color: #161616;
}

/* Cover Art Frame & Hover Overlay */
eventbox.cover-eventbox {
    background-color: #141414;
    border: 1px solid #282828;
    border-radius: 6px;
}

box.cover-overlay-box {
    background-color: rgba(6, 6, 6, 0.92);
    border-radius: 6px;
    padding: 8px;
}

label.overlay-title {
    color: #FFFFFF;
    font-family: "JetBrainsMono Nerd Font", "JetBrains Mono", monospace;
    font-size: 10.5px;
    font-weight: bold;
}

label.overlay-artist {
    color: #50FA7B;
    font-family: "JetBrainsMono Nerd Font", "JetBrains Mono", monospace;
    font-size: 9px;
    font-weight: 500;
}

label.overlay-album {
    color: #888888;
    font-family: "JetBrainsMono Nerd Font", "JetBrains Mono", monospace;
    font-size: 8px;
}

label.overlay-tag {
    background-color: #181818;
    border: 1px solid #303030;
    border-radius: 3px;
    color: #A0A0A0;
    font-family: "JetBrainsMono Nerd Font", "JetBrains Mono", monospace;
    font-size: 8px;
    padding: 1px 4px;
}

/* Center Transport Controls */
button.transport-btn {
    background-color: #121212;
    border: 1px solid #282828;
    border-radius: 5px;
    color: #A0A0A0;
    font-family: "JetBrainsMono Nerd Font", "JetBrains Mono", monospace;
    font-size: 11px;
    padding: 4px 8px;
}

button.transport-btn:hover {
    background-color: #1e1e1e;
    color: #FFFFFF;
    border-color: #484848;
}

button.main-play-btn {
    background-color: #50FA7B;
    border: 1px solid #50FA7B;
    border-radius: 18px;
    color: #000000;
    font-size: 12px;
    font-weight: bold;
    padding: 5px 14px;
}

button.main-play-btn:hover {
    background-color: #69ff91;
    border-color: #69ff91;
    color: #000000;
}

/* Sliders */
scale trough {
    background-color: #202020;
    border-radius: 2px;
    min-height: 4px;
}

scale highlight {
    background-color: #50FA7B;
    border-radius: 2px;
    min-height: 4px;
}

scale slider {
    background-color: #FFFFFF;
    border-radius: 50%;
    min-width: 9px;
    min-height: 9px;
    margin: -3px;
}

scale.vol-scale trough {
    background-color: #202020;
    border-radius: 2px;
    min-height: 3px;
}

scale.vol-scale highlight {
    background-color: #888888;
    border-radius: 2px;
    min-height: 3px;
}

scale.vol-scale slider {
    background-color: #D4D4D4;
    border-radius: 50%;
    min-width: 7px;
    min-height: 7px;
    margin: -2px;
}

label.time-label {
    color: #707070;
    font-family: "JetBrainsMono Nerd Font", "JetBrains Mono", monospace;
    font-size: 8.5px;
}

/* Tab Bar */
button.tab-nav-btn {
    background-color: #121212;
    border: 1px solid #242424;
    border-radius: 5px;
    color: #808080;
    font-family: "JetBrainsMono Nerd Font", "JetBrains Mono", monospace;
    font-size: 9px;
    padding: 2px 8px;
}

button.tab-nav-btn:hover {
    color: #D4D4D4;
    background-color: #1a1a1a;
}

button.tab-nav-btn.tab-active {
    background-color: #18261d;
    border-color: #50FA7B;
    color: #50FA7B;
    font-weight: bold;
}

/* Scrolled Windows & Listbox Resets */
scrolledwindow,
scrolledwindow viewport,
viewport,
list,
row {
    background-color: transparent;
    background: transparent;
    background-image: none;
    border: none;
    box-shadow: none;
    outline: none;
}

scrolledwindow.glass-scroll {
    border: 1px solid #1a1a1a;
    border-radius: 5px;
}

row.song-row {
    background-color: transparent;
    border-bottom: 1px solid #151515;
    padding: 2px 5px;
}

row.song-row:hover {
    background-color: #161616;
}

row.song-row:selected {
    background-color: #15241b;
}

label.row-title {
    color: #D4D4D4;
    font-family: "JetBrainsMono Nerd Font", "JetBrains Mono", monospace;
    font-size: 9px;
    font-weight: 500;
}

label.row-artist {
    color: #707070;
    font-family: "JetBrainsMono Nerd Font", "JetBrains Mono", monospace;
    font-size: 8px;
}

/* Lyrics Display */
box.lyrics-line-box {
    padding: 3px 6px;
    border-radius: 4px;
}

label.lyrics-line-inactive {
    color: #606060;
    font-family: "JetBrainsMono Nerd Font", "JetBrains Mono", monospace;
    font-size: 9.5px;
}

label.lyrics-line-active {
    color: #50FA7B;
    font-family: "JetBrainsMono Nerd Font", "JetBrains Mono", monospace;
    font-size: 11px;
    font-weight: bold;
}

separator {
    background-color: #202020;
}
"""

# -----------------------------------------------------------------------------
# JIOSAAVN API HELPERS & DES DECRYPTION
# -----------------------------------------------------------------------------
def decrypt_saavn_url(encrypted_url):
    if not encrypted_url:
        return None
    try:
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            key = b"38346591" * 3
            cipher = Cipher(algorithms.TripleDES(key), modes.ECB(), backend=default_backend())
            decryptor = cipher.decryptor()
            enc_bytes = base64.b64decode(encrypted_url.strip())
            dec = decryptor.update(enc_bytes) + decryptor.finalize()
            pad_len = dec[-1]
            if isinstance(pad_len, int) and 0 < pad_len <= 8:
                dec = dec[:-pad_len]
            url = dec.decode("utf-8", errors="ignore")
            return url
    except Exception:
        pass
    return None

def get_stream_urls(encrypted_url, preview_url=""):
    urls = []
    base_url = decrypt_saavn_url(encrypted_url)
    if base_url:
        for ext in ["_320.mp4", "_160.mp4", "_96.mp4", "_48.mp4"]:
            candidate = re.sub(r'_(?:320|160|96|48|128)\.mp4$', ext, base_url)
            if candidate not in urls:
                urls.append(candidate)
        if base_url not in urls:
            urls.append(base_url)
    if preview_url and preview_url not in urls:
        urls.append(preview_url)
    return urls

def fetch_json(url, timeout=6):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        content = resp.read().decode("utf-8", errors="ignore")
        if content.startswith("<!--") and "-->" in content:
            content = content[content.find("-->") + 3:]
        return json.loads(content.strip())

def search_jiosaavn(query, count=25):
    q_enc = urllib.parse.quote(query.strip())
    url = f"https://www.jiosaavn.com/api.php?__call=search.getResults&_format=json&p=1&n={count}&q={q_enc}"
    try:
        data = fetch_json(url)
        results = data.get("results", [])
        songs = []
        for s in results:
            enc_url = s.get("encrypted_media_url")
            preview_url = s.get("media_preview_url", "")
            stream_urls = get_stream_urls(enc_url, preview_url)
            stream_url = stream_urls[0] if stream_urls else (preview_url or "")
            img_url = s.get("image", "").replace("150x150", "500x500")
            title = s.get("song") or s.get("title", "Unknown Track")
            title = title.replace("&quot;", '"').replace("&amp;", "&").replace("&#039;", "'")
            artist = s.get("primary_artists") or s.get("singers") or s.get("music", "Various Artists")
            artist = artist.replace("&quot;", '"').replace("&amp;", "&").replace("&#039;", "'")
            album = s.get("album", "")
            album = album.replace("&quot;", '"').replace("&amp;", "&").replace("&#039;", "'")
            
            try:
                duration = int(s.get("duration", 0))
            except Exception:
                duration = 0
                
            songs.append({
                "id": s.get("id"),
                "title": title,
                "artist": artist,
                "album": album,
                "year": s.get("year", ""),
                "language": s.get("language", "").capitalize(),
                "image": img_url,
                "stream_url": stream_url,
                "stream_urls": stream_urls,
                "encrypted_media_url": enc_url,
                "duration": duration,
                "is_offline": False
            })
        return songs
    except Exception as e:
        print(f"[MusicPlayer] Search error for '{query}': {e}")
        return []

def fetch_lyrics_data(song):
    song_id = song.get("id")
    title = song.get("title", "")
    artist = song.get("artist", "").split(",")[0].strip()
    
    # Try LRCLIB for synced karaoke lyrics
    try:
        q_title = urllib.parse.quote(title)
        q_artist = urllib.parse.quote(artist)
        url = f"https://lrclib.net/api/get?artist_name={q_artist}&track_name={q_title}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            ldata = json.loads(resp.read().decode())
            if ldata.get("syncedLyrics"):
                synced = []
                for line in ldata["syncedLyrics"].splitlines():
                    m = re.match(r'\[(\d+):(\d+\.?\d*)\](.*)', line)
                    if m:
                        mm = int(m.group(1))
                        ss = float(m.group(2))
                        total_sec = mm * 60 + ss
                        txt = m.group(3).strip()
                        if txt:
                            synced.append((total_sec, txt))
                if synced:
                    return {"type": "synced", "lines": synced}
            if ldata.get("plainLyrics"):
                lines = [l.strip() for l in ldata["plainLyrics"].splitlines() if l.strip()]
                return {"type": "plain", "lines": [(i * 4, l) for i, l in enumerate(lines)]}
    except Exception:
        pass

    # Try JioSaavn plain lyrics
    if song_id:
        try:
            url = f"https://www.jiosaavn.com/api.php?__call=lyrics.getLyrics&ctx=web6dot0&api_version=4&_format=json&_marker=0%3F_marker%3D0&lyrics_id={song_id}"
            data = fetch_json(url, timeout=4)
            lyrics = data.get("lyrics", "")
            if lyrics and len(lyrics.strip()) > 10:
                lyrics_clean = lyrics.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
                lyrics_clean = lyrics_clean.replace("&quot;", '"').replace("&amp;", "&").replace("&#039;", "'")
                lines = [l.strip() for l in lyrics_clean.splitlines() if l.strip()]
                return {"type": "plain", "lines": [(i * 4, l) for i, l in enumerate(lines)]}
        except Exception:
            pass

    return {
        "type": "plain",
        "lines": [(0, f"♪ {title} ♪"), (4, f"By {artist}"), (8, "Lyrics not available")]
    }


def check_internet_connection(timeout=1.5):
    """Fast non-blocking socket test to verify real internet connectivity."""
    endpoints = [
        ("1.1.1.1", 53),
        ("8.8.8.8", 53),
        ("www.jiosaavn.com", 443)
    ]
    for host, port in endpoints:
        try:
            s = socket.create_connection((host, port), timeout=timeout)
            s.close()
            return True
        except (socket.timeout, socket.error, OSError):
            continue
    return False


# -----------------------------------------------------------------------------
# MAIN DESKTOP MUSIC PLAYER CLASS
# -----------------------------------------------------------------------------
class DesktopMusicPlayer(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_title("Desktop Music Player")
        self.set_wmclass("DesktopMusicPlayer", "DesktopMusicPlayer")
        
        # Window attributes (Desktop widget layer below normal windows)
        self.set_decorated(False)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_keep_below(True)
        self.set_focus_on_map(False)
        self.stick()
        
        # Transparency
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.set_visual(visual)
            
        # GStreamer Audio Engine
        self.player = Gst.ElementFactory.make("playbin", "music_player")
        self.bus = self.player.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect("message", self.on_gst_message)
        
        # State
        self.playlist = []
        self.current_index = -1
        self.is_playing = False
        self.is_seeking = False
        self.shuffle_mode = False
        self.repeat_mode = 0  # 0: Off, 1: Repeat All, 2: Repeat One
        self.volume = 0.85
        self.player.set_property("volume", self.volume)
        
        # Wave animation & Theme color state
        self.wave_phase = 0.0
        self.theme_color = (0.31, 0.98, 0.48)
        self.wave_timer = None
        
        # Lyrics State
        self.current_lyrics = None
        self.current_lyric_idx = -1
        self.lyric_label_widgets = []
        
        # Offline & Liked state
        self.liked_songs = get_liked_songs()
        self.view_mode = "search"
        self.current_query = "The Weeknd"
        self._fallback_url_idx = 0
        self.downloading_ids = set()
        self.is_online = True
        self._checking_network = False
        
        # Target Dimensions strictly matching combined left widgets
        self.TARGET_HEIGHT = 310
        
        self.load_css()
        self.build_ui()
        
        # Signals
        self.connect("realize", self.on_realize)
        self.connect("key-press-event", self.on_key_press)
        
        # Timers
        GLib.timeout_add(250, self.update_playback_progress)
        self.wave_timer = GLib.timeout_add(50, self.update_ambient_wave)
        GLib.timeout_add_seconds(3, self._periodic_network_check)
        
        # Initial Internet Verification & Category Load
        self.check_network_async()
        threading.Thread(target=self.load_query, args=(self.current_query,), daemon=True).start()

    def load_css(self):
        self.get_style_context().add_class("desktop-music-window")
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS_DATA.encode("utf-8"))
        Gtk.StyleContext.add_provider_for_screen(
            self.get_screen(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_USER
        )

    def build_ui(self):
        # The main card fills the entire window (310px height) so the border matches left widgets
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.main_box.get_style_context().add_class("music-card")
        
        # ---------------------------------------------------------------------
        # 0. AMBIENT MUSIC WAVE (Integrated as glowing top wave inside the card)
        # ---------------------------------------------------------------------
        self.ambient_wave_area = Gtk.DrawingArea()
        self.ambient_wave_area.set_size_request(-1, 8)
        self.ambient_wave_area.connect("draw", self.draw_ambient_wave)
        self.main_box.pack_start(self.ambient_wave_area, False, False, 0)
        
        # ---------------------------------------------------------------------
        # 1. TOP UTILITY BAR (Options: Like, Download, Offline, Quality + Search)
        # ---------------------------------------------------------------------
        top_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        # Logo & Online Indicator
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.lbl_title = Gtk.Label()
        self.lbl_title.set_markup("<b>󰎆 Music</b>")
        self.lbl_title.get_style_context().add_class("header-title")
        title_box.pack_start(self.lbl_title, False, False, 0)
        
        self.lbl_status = Gtk.Label(label="● ONLINE")
        self.lbl_status.get_style_context().add_class("status-badge")
        title_box.pack_start(self.lbl_status, False, False, 0)
        top_bar.pack_start(title_box, False, False, 0)
        
        # Action Options Center Box
        options_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        self.btn_refresh = Gtk.Button(label="󰑐 Refresh")
        self.btn_refresh.get_style_context().add_class("action-opt-btn")
        self.btn_refresh.set_tooltip_text("Refresh playback & reload playlist (Ctrl+R / F5)")
        self.btn_refresh.connect("clicked", self.on_refresh_clicked)
        options_box.pack_start(self.btn_refresh, False, False, 0)
        
        self.btn_like = Gtk.Button(label="󰣐 Like")
        self.btn_like.get_style_context().add_class("action-opt-btn")
        self.btn_like.set_tooltip_text("Favorite track / Add to Liked")
        self.btn_like.connect("clicked", self.on_like_toggle)
        options_box.pack_start(self.btn_like, False, False, 0)
        
        self.btn_liked_list = Gtk.Button(label=f"󰋑 Liked ({len(self.liked_songs)})")
        self.btn_liked_list.get_style_context().add_class("action-opt-btn")
        self.btn_liked_list.set_tooltip_text("Show Liked Songs Playlist")
        self.btn_liked_list.connect("clicked", self.show_liked_playlist)
        options_box.pack_start(self.btn_liked_list, False, False, 0)
        
        self.btn_download = Gtk.Button(label="󰇚 Download 320k")
        self.btn_download.get_style_context().add_class("action-opt-btn")
        self.btn_download.set_tooltip_text("Download high quality audio offline")
        self.btn_download.connect("clicked", self.on_download_current)
        options_box.pack_start(self.btn_download, False, False, 0)
        
        self.btn_offline = Gtk.Button(label="󰋋 Offline Library")
        self.btn_offline.get_style_context().add_class("action-opt-btn")
        self.btn_offline.set_tooltip_text("Play downloaded offline tracks")
        self.btn_offline.connect("clicked", self.show_offline_library)
        options_box.pack_start(self.btn_offline, False, False, 0)
        
        self.btn_quality = Gtk.Button(label="󰓃 320K HQ")
        self.btn_quality.get_style_context().add_class("action-opt-btn")
        options_box.pack_start(self.btn_quality, False, False, 0)
        
        top_bar.pack_start(options_box, True, True, 0)
        
        # Search Entry
        self.search_entry = Gtk.Entry()
        self.search_entry.set_placeholder_text("󰍉 Search songs, Gujarati, Artists...")
        self.search_entry.get_style_context().add_class("search-entry")
        self.search_entry.set_width_chars(24)
        self.search_entry.connect("activate", self.on_search_activate)
        top_bar.pack_start(self.search_entry, False, False, 0)
        
        self.main_box.pack_start(top_bar, False, False, 0)
        
        sep1 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.main_box.pack_start(sep1, False, False, 0)
        
        # ---------------------------------------------------------------------
        # 2. MAIN 3-PANEL BODY (Height perfectly fills remaining space)
        # ---------------------------------------------------------------------
        content_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        
        # === LEFT PANEL: CLEAN SQUARE COVER ART WITH HOVER OVERLAY ===
        self.cover_size = 180
        self.cover_eventbox = Gtk.EventBox()
        self.cover_eventbox.get_style_context().add_class("cover-eventbox")
        self.cover_eventbox.set_size_request(self.cover_size, self.cover_size)
        self.cover_eventbox.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)
        self.cover_eventbox.connect("enter-notify-event", self.on_cover_enter)
        self.cover_eventbox.connect("leave-notify-event", self.on_cover_leave)
        
        self.cover_overlay = Gtk.Overlay()
        
        # 1. Base Image Layer
        self.img_cover = Gtk.Image()
        self.set_default_cover_art()
        self.cover_overlay.add(self.img_cover)
        
        # 2. Hover Information Card Layer (Overlaid on top of image)
        self.overlay_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.overlay_card.get_style_context().add_class("cover-overlay-box")
        self.overlay_card.set_valign(Gtk.Align.FILL)
        self.overlay_card.set_halign(Gtk.Align.FILL)
        
        self.lbl_ov_title = Gtk.Label(label="No Track")
        self.lbl_ov_title.get_style_context().add_class("overlay-title")
        self.lbl_ov_title.set_xalign(0.0)
        self.lbl_ov_title.set_ellipsize(Pango.EllipsizeMode.END)
        self.lbl_ov_title.set_max_width_chars(20)
        self.overlay_card.pack_start(self.lbl_ov_title, False, False, 0)
        
        self.lbl_ov_artist = Gtk.Label(label="Select a song")
        self.lbl_ov_artist.get_style_context().add_class("overlay-artist")
        self.lbl_ov_artist.set_xalign(0.0)
        self.lbl_ov_artist.set_ellipsize(Pango.EllipsizeMode.END)
        self.lbl_ov_artist.set_max_width_chars(20)
        self.overlay_card.pack_start(self.lbl_ov_artist, False, False, 0)
        
        self.lbl_ov_album = Gtk.Label(label="JioSaavn HD")
        self.lbl_ov_album.get_style_context().add_class("overlay-album")
        self.lbl_ov_album.set_xalign(0.0)
        self.lbl_ov_album.set_ellipsize(Pango.EllipsizeMode.END)
        self.lbl_ov_album.set_max_width_chars(20)
        self.overlay_card.pack_start(self.lbl_ov_album, False, False, 0)
        
        tags_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.lbl_ov_bitrate = Gtk.Label(label="320 KBPS")
        self.lbl_ov_bitrate.get_style_context().add_class("overlay-tag")
        tags_row.pack_start(self.lbl_ov_bitrate, False, False, 0)
        
        self.lbl_ov_lang = Gtk.Label(label="ORIGINAL")
        self.lbl_ov_lang.get_style_context().add_class("overlay-tag")
        tags_row.pack_start(self.lbl_ov_lang, False, False, 0)
        self.overlay_card.pack_start(tags_row, False, False, 2)
        
        self.overlay_card.pack_start(Gtk.Box(), True, True, 0)
        
        # Quick Actions on Hover
        ov_actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.btn_ov_like = Gtk.Button(label="󰣐 Like")
        self.btn_ov_like.get_style_context().add_class("action-opt-btn")
        self.btn_ov_like.connect("clicked", self.on_like_toggle)
        ov_actions.pack_start(self.btn_ov_like, True, True, 0)
        
        self.btn_ov_dl = Gtk.Button(label="󰇚 Save")
        self.btn_ov_dl.get_style_context().add_class("action-opt-btn")
        self.btn_ov_dl.connect("clicked", self.on_download_current)
        ov_actions.pack_start(self.btn_ov_dl, True, True, 0)
        self.overlay_card.pack_start(ov_actions, False, False, 0)
        
        self.cover_overlay.add_overlay(self.overlay_card)
        self.overlay_card.set_no_show_all(True)
        self.overlay_card.hide()
        
        self.cover_eventbox.add(self.cover_overlay)
        content_box.pack_start(self.cover_eventbox, False, False, 0)
        
        sep_v1 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        content_box.pack_start(sep_v1, False, False, 0)
        
        # === CENTER PANEL: TRANSPORT CONTROLS & TIME PROGRESS ===
        center_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        center_panel.set_valign(Gtk.Align.CENTER)
        center_panel.set_size_request(380, -1)
        
        center_meta = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.lbl_center_title = Gtk.Label(label="No Track Loaded")
        self.lbl_center_title.get_style_context().add_class("overlay-title")
        self.lbl_center_title.set_ellipsize(Pango.EllipsizeMode.END)
        self.lbl_center_title.set_max_width_chars(32)
        center_meta.pack_start(self.lbl_center_title, False, False, 0)
        
        self.lbl_center_artist = Gtk.Label(label="Search or select a song to start")
        self.lbl_center_artist.get_style_context().add_class("row-artist")
        self.lbl_center_artist.set_ellipsize(Pango.EllipsizeMode.END)
        self.lbl_center_artist.set_max_width_chars(36)
        center_meta.pack_start(self.lbl_center_artist, False, False, 0)
        center_panel.pack_start(center_meta, False, False, 0)
        
        # Transport Buttons
        ctrl_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        ctrl_box.set_halign(Gtk.Align.CENTER)
        
        self.btn_shuffle = Gtk.Button(label="󰒝")
        self.btn_shuffle.get_style_context().add_class("transport-btn")
        self.btn_shuffle.set_tooltip_text("Shuffle Mode")
        self.btn_shuffle.connect("clicked", self.toggle_shuffle)
        ctrl_box.pack_start(self.btn_shuffle, False, False, 0)
        
        self.btn_prev = Gtk.Button(label="󰒮")
        self.btn_prev.get_style_context().add_class("transport-btn")
        self.btn_prev.set_tooltip_text("Previous Track")
        self.btn_prev.connect("clicked", self.play_previous)
        ctrl_box.pack_start(self.btn_prev, False, False, 0)
        
        self.btn_play = Gtk.Button(label="󰐊")
        self.btn_play.get_style_context().add_class("main-play-btn")
        self.btn_play.set_tooltip_text("Play / Pause (Space)")
        self.btn_play.connect("clicked", self.toggle_play_pause)
        ctrl_box.pack_start(self.btn_play, False, False, 0)
        
        self.btn_next = Gtk.Button(label="󰒭")
        self.btn_next.get_style_context().add_class("transport-btn")
        self.btn_next.set_tooltip_text("Next Track")
        self.btn_next.connect("clicked", self.play_next)
        ctrl_box.pack_start(self.btn_next, False, False, 0)
        
        self.btn_repeat = Gtk.Button(label="󰑖")
        self.btn_repeat.get_style_context().add_class("transport-btn")
        self.btn_repeat.set_tooltip_text("Repeat (Off / All / One)")
        self.btn_repeat.connect("clicked", self.toggle_repeat)
        ctrl_box.pack_start(self.btn_repeat, False, False, 0)
        center_panel.pack_start(ctrl_box, False, False, 0)
        
        # Progress Bar & Time
        progress_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.lbl_curr_time = Gtk.Label(label="00:00")
        self.lbl_curr_time.get_style_context().add_class("time-label")
        progress_box.pack_start(self.lbl_curr_time, False, False, 0)
        
        self.progress_adj = Gtk.Adjustment(value=0, lower=0, upper=100, step_increment=1, page_increment=5)
        self.progress_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.progress_adj)
        self.progress_scale.set_draw_value(False)
        self.progress_scale.connect("button-press-event", self.on_seek_start)
        self.progress_scale.connect("button-release-event", self.on_seek_end)
        self.progress_scale.connect("change-value", self.on_seek_change)
        progress_box.pack_start(self.progress_scale, True, True, 0)
        
        self.lbl_total_time = Gtk.Label(label="00:00")
        self.lbl_total_time.get_style_context().add_class("time-label")
        progress_box.pack_start(self.lbl_total_time, False, False, 0)
        center_panel.pack_start(progress_box, False, False, 0)
        
        # Volume & Helpers
        bottom_tools = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        bottom_tools.set_halign(Gtk.Align.CENTER)
        
        self.btn_mute = Gtk.Button(label="󰕾")
        self.btn_mute.get_style_context().add_class("transport-btn")
        self.btn_mute.connect("clicked", self.toggle_mute)
        bottom_tools.pack_start(self.btn_mute, False, False, 0)
        
        self.vol_adj = Gtk.Adjustment(value=self.volume * 100, lower=0, upper=100, step_increment=5, page_increment=10)
        self.vol_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.vol_adj)
        self.vol_scale.set_draw_value(False)
        self.vol_scale.set_size_request(80, -1)
        self.vol_scale.get_style_context().add_class("vol-scale")
        self.vol_scale.connect("value-changed", self.on_volume_changed)
        bottom_tools.pack_start(self.vol_scale, False, False, 0)
        
        self.lbl_vol_pct = Gtk.Label(label=f"{int(self.volume*100)}%")
        self.lbl_vol_pct.get_style_context().add_class("time-label")
        bottom_tools.pack_start(self.lbl_vol_pct, False, False, 0)
        center_panel.pack_start(bottom_tools, False, False, 0)
        
        content_box.pack_start(center_panel, True, True, 0)
        
        sep_v2 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        content_box.pack_start(sep_v2, False, False, 0)
        
        # === RIGHT PANEL: MINIMAL QUEUE & BEAUTIFUL KARAOKE LYRICS ===
        right_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        right_panel.set_size_request(410, -1)
        
        # Tab Bar
        tab_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        self.btn_tab_queue = Gtk.Button(label="󰒺 Queue (0)")
        self.btn_tab_queue.get_style_context().add_class("tab-nav-btn")
        self.btn_tab_queue.get_style_context().add_class("tab-active")
        self.btn_tab_queue.connect("clicked", self.show_queue_tab)
        tab_header.pack_start(self.btn_tab_queue, True, True, 0)
        
        self.btn_tab_lyrics = Gtk.Button(label="󰎆 Live Lyrics")
        self.btn_tab_lyrics.get_style_context().add_class("tab-nav-btn")
        self.btn_tab_lyrics.connect("clicked", self.show_lyrics_tab)
        tab_header.pack_start(self.btn_tab_lyrics, True, True, 0)
        
        right_panel.pack_start(tab_header, False, False, 0)
        
        # Stack Container
        self.right_stack = Gtk.Stack()
        self.right_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.right_stack.set_transition_duration(100)
        
        # 1. Queue View
        self.scroll_queue = Gtk.ScrolledWindow()
        self.scroll_queue.get_style_context().add_class("glass-scroll")
        self.scroll_queue.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scroll_queue.set_min_content_height(175)
        self.scroll_queue.set_max_content_height(175)
        
        self.list_queue = Gtk.ListBox()
        self.list_queue.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.list_queue.connect("row-activated", self.on_queue_row_activated)
        self.scroll_queue.add(self.list_queue)
        self.right_stack.add_named(self.scroll_queue, "queue")
        
        # 2. Enhanced Lyrics View (Line-by-line Synced Karaoke Box)
        self.scroll_lyrics = Gtk.ScrolledWindow()
        self.scroll_lyrics.get_style_context().add_class("glass-scroll")
        self.scroll_lyrics.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scroll_lyrics.set_min_content_height(175)
        self.scroll_lyrics.set_max_content_height(175)
        
        self.lyrics_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.lyrics_container.set_valign(Gtk.Align.CENTER)
        self.lyrics_container.set_halign(Gtk.Align.CENTER)
        self.scroll_lyrics.add(self.lyrics_container)
        self.right_stack.add_named(self.scroll_lyrics, "lyrics")
        
        right_panel.pack_start(self.right_stack, True, True, 0)
        content_box.pack_start(right_panel, False, False, 0)
        
        self.main_box.pack_start(content_box, True, True, 0)
        self.add(self.main_box)

    # -------------------------------------------------------------------------
    # HOVER OVERLAY EVENTS ON SQUARE ALBUM COVER
    # -------------------------------------------------------------------------
    def on_cover_enter(self, widget, event):
        self.overlay_card.show_all()

    def on_cover_leave(self, widget, event):
        self.overlay_card.hide()

    def set_default_cover_art(self):
        pix = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, self.cover_size, self.cover_size)
        pix.fill(0x141414FF)
        self.img_cover.set_from_pixbuf(pix)

    def load_cover_art_from_url(self, url):
        def _fetch():
            try:
                cache_file = os.path.join(CACHE_IMG_DIR, f"{hash(url)}.jpg")
                if not os.path.exists(cache_file):
                    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=5) as resp:
                        data = resp.read()
                        with open(cache_file, "wb") as f:
                            f.write(data)
                
                pix = GdkPixbuf.Pixbuf.new_from_file_at_scale(cache_file, self.cover_size, self.cover_size, False)
                if pix:
                    GLib.idle_add(self.img_cover.set_from_pixbuf, pix)
                    GLib.idle_add(self.extract_theme_color, pix)
            except Exception:
                GLib.idle_add(self.set_default_cover_art)
        threading.Thread(target=_fetch, daemon=True).start()

    def extract_theme_color(self, pixbuf):
        try:
            pixels = pixbuf.get_pixels()
            n_channels = pixbuf.get_n_channels()
            rowstride = pixbuf.get_rowstride()
            w = pixbuf.get_width()
            h = pixbuf.get_height()
            
            r_total, g_total, b_total, count = 0, 0, 0, 0
            step = 10
            for y in range(0, h, step):
                for x in range(0, w, step):
                    idx = y * rowstride + x * n_channels
                    r = pixels[idx]
                    g = pixels[idx + 1]
                    b = pixels[idx + 2]
                    if max(r, g, b) > 50 and (max(r, g, b) - min(r, g, b)) > 20:
                        r_total += r
                        g_total += g
                        b_total += b
                        count += 1
                        
            if count > 0:
                self.theme_color = (
                    min(1.0, (r_total / count) / 255.0 * 1.2),
                    min(1.0, (g_total / count) / 255.0 * 1.2),
                    min(1.0, (b_total / count) / 255.0 * 1.2)
                )
            else:
                self.theme_color = (0.31, 0.98, 0.48)
        except Exception:
            self.theme_color = (0.31, 0.98, 0.48)

    # -------------------------------------------------------------------------
    # AMBIENT MUSIC WAVE DRAWING (Multi-layer smooth sine waves, 0.3-0.4 opacity)
    # -------------------------------------------------------------------------
    def draw_ambient_wave(self, widget, cr):
        w = widget.get_allocated_width()
        h = widget.get_allocated_height()
        
        if w <= 0 or h <= 0:
            return False
            
        r, g, b = self.theme_color
        
        wave_layers = [
            {"freq": 0.015, "speed": 1.0, "amp": 3.0 if self.is_playing else 1.2, "alpha": 0.38, "offset": 0},
            {"freq": 0.025, "speed": 1.4, "amp": 2.2 if self.is_playing else 0.8, "alpha": 0.32, "offset": math.pi / 3},
            {"freq": 0.008, "speed": 0.7, "amp": 2.5 if self.is_playing else 1.0, "alpha": 0.28, "offset": math.pi / 1.5}
        ]
        
        for layer in wave_layers:
            cr.set_source_rgba(r, g, b, layer["alpha"])
            cr.set_line_width(1.4)
            
            phase = self.wave_phase * layer["speed"] + layer["offset"]
            cr.move_to(0, h / 2)
            
            step = 4
            for x in range(0, w + step, step):
                envelope = math.sin((x / w) * math.pi)
                y = (h / 2) + math.sin(x * layer["freq"] + phase) * layer["amp"] * envelope
                cr.line_to(x, y)
                
            cr.stroke()
        return False

    def update_ambient_wave(self):
        speed = 0.08 if self.is_playing else 0.02
        self.wave_phase += speed
        if self.wave_phase > 2 * math.pi * 10:
            self.wave_phase = 0.0
            
        self.ambient_wave_area.queue_draw()
        return True

    # -------------------------------------------------------------------------
    # TAB NAVIGATION (Queue & Synced Lyrics)
    # -------------------------------------------------------------------------
    def show_queue_tab(self, widget):
        self.right_stack.set_visible_child_name("queue")
        self.btn_tab_queue.get_style_context().add_class("tab-active")
        self.btn_tab_lyrics.get_style_context().remove_class("tab-active")

    def show_lyrics_tab(self, widget):
        self.right_stack.set_visible_child_name("lyrics")
        self.btn_tab_lyrics.get_style_context().add_class("tab-active")
        self.btn_tab_queue.get_style_context().remove_class("tab-active")

    # -------------------------------------------------------------------------
    # INTERNET CONNECTIVITY & STATUS BADGE SYSTEM
    # -------------------------------------------------------------------------
    def set_status(self, text=None, style_type=None):
        """Update the status badge label, style class, and helpful tooltip."""
        ctx = self.lbl_status.get_style_context()
        ctx.remove_class("status-online")
        ctx.remove_class("status-offline")
        ctx.remove_class("status-busy")

        if text is None:
            if self.is_online:
                text = "● ONLINE"
                style_type = "online"
            else:
                text = "● OFFLINE"
                style_type = "offline"

        if style_type is None:
            if "OFFLINE" in text or "ERROR" in text or "FAILED" in text:
                style_type = "offline"
            elif "ONLINE" in text or "DOWNLOADED" in text:
                style_type = "online"
            else:
                style_type = "busy"

        if style_type == "online":
            ctx.add_class("status-online")
            self.lbl_status.set_tooltip_text("Internet Status: Connected (Online Streaming & Search Ready)")
        elif style_type == "offline":
            ctx.add_class("status-offline")
            self.lbl_status.set_tooltip_text("Internet Status: Offline (No Internet Connection - Offline Library Available)")
        elif style_type == "busy":
            ctx.add_class("status-busy")

        self.lbl_status.set_text(text)

    def _periodic_network_check(self):
        self.check_network_async()
        return True

    def check_network_async(self, callback=None):
        if self._checking_network:
            return
        self._checking_network = True

        def _worker():
            try:
                online = check_internet_connection()
                GLib.idle_add(self.apply_network_status, online)
                if callback:
                    GLib.idle_add(callback, online)
            except Exception:
                pass
            finally:
                self._checking_network = False

        threading.Thread(target=_worker, daemon=True).start()

    def apply_network_status(self, is_online):
        prev = self.is_online
        self.is_online = bool(is_online)
        self.set_status()

    # -------------------------------------------------------------------------
    # SEARCH, LIKE & OFFLINE ENGINE
    # -------------------------------------------------------------------------
    def on_refresh_clicked(self, widget=None):
        """Full refresh: Checks internet, recovers audio engine, and reloads current view."""
        self.set_status("● REFRESHING...", "busy")
        self.btn_refresh.get_style_context().add_class("btn-refresh-active")
        
        def _do_refresh():
            online = check_internet_connection()
            GLib.idle_add(self.apply_network_status, online)
            
            # Reset GStreamer pipeline
            try:
                self.player.set_state(Gst.State.NULL)
            except Exception:
                pass
                
            if self.view_mode == "offline":
                GLib.idle_add(self.show_offline_library, None)
            elif self.view_mode == "liked":
                self.liked_songs = get_liked_songs()
                GLib.idle_add(self.show_liked_playlist, None)
            else:
                if online:
                    q = self.search_entry.get_text().strip() or getattr(self, "current_query", "The Weeknd")
                    self.load_query(q)
                else:
                    GLib.idle_add(self.show_offline_library, None)
                    
            GLib.idle_add(self.reposition_between_widgets)
            
            if 0 <= self.current_index < len(self.playlist):
                GLib.timeout_add(400, lambda: self.load_song_index(self.current_index, auto_play=True) or False)
                
            GLib.timeout_add(800, lambda: self.btn_refresh.get_style_context().remove_class("btn-refresh-active") or False)
            GLib.timeout_add(1200, lambda: self.set_status() or False)

        threading.Thread(target=_do_refresh, daemon=True).start()

    def on_search_activate(self, entry):
        text = entry.get_text().strip()
        if text:
            self.current_query = text
            self.view_mode = "search"
            self.btn_liked_list.get_style_context().remove_class("btn-liked-active")
            self.btn_offline.get_style_context().remove_class("btn-offline-active")
            threading.Thread(target=self.load_query, args=(text,), daemon=True).start()

    def load_query(self, query):
        self.current_query = query
        self.set_status("● SEARCHING...", "busy")
        
        def _fetch():
            online = check_internet_connection()
            GLib.idle_add(self.apply_network_status, online)
            
            if not online:
                GLib.idle_add(self.populate_playlist, [], f"Results for '{query}'")
                return

            songs = search_jiosaavn(query, count=25)
            if not songs and not check_internet_connection():
                GLib.idle_add(self.apply_network_status, False)
            GLib.idle_add(self.populate_playlist, songs, f"Results for '{query}'")

        threading.Thread(target=_fetch, daemon=True).start()

    def populate_playlist(self, songs, header_title="Playlist"):
        self.playlist = songs
        self.btn_tab_queue.set_label(f"󰒺 Queue ({len(songs)})")
        
        for child in self.list_queue.get_children():
            self.list_queue.remove(child)
            
        if not songs:
            row = Gtk.ListBoxRow()
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
            box.set_margin_top(18)
            box.set_margin_bottom(18)
            box.set_halign(Gtk.Align.CENTER)
            
            if not self.is_online:
                lbl = Gtk.Label(label="● Offline: No Internet Connection")
                lbl.get_style_context().add_class("status-badge")
                lbl.get_style_context().add_class("status-offline")
                box.pack_start(lbl, False, False, 0)
                
                sub_lbl = Gtk.Label(label="Internet is off. Play songs from your Offline Library.")
                sub_lbl.get_style_context().add_class("row-artist")
                box.pack_start(sub_lbl, False, False, 0)
                
                btn_go_offline = Gtk.Button(label="󰋋 Open Offline Library")
                btn_go_offline.get_style_context().add_class("action-opt-btn")
                btn_go_offline.get_style_context().add_class("btn-offline-active")
                btn_go_offline.connect("clicked", self.show_offline_library)
                box.pack_start(btn_go_offline, False, False, 4)
            else:
                lbl = Gtk.Label(label=f"No songs found in {header_title}")
                lbl.get_style_context().add_class("row-artist")
                box.pack_start(lbl, False, False, 0)
                
            row.add(box)
            self.list_queue.add(row)
            self.list_queue.show_all()
            self.set_status()
            return
            
        for idx, s in enumerate(songs):
            row = Gtk.ListBoxRow()
            row.get_style_context().add_class("song-row")
            
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            
            num_lbl = Gtk.Label(label=f"{idx+1:02d}")
            num_lbl.get_style_context().add_class("time-label")
            num_lbl.set_size_request(18, -1)
            box.pack_start(num_lbl, False, False, 0)
            
            info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
            t_lbl = Gtk.Label(label=s["title"])
            t_lbl.get_style_context().add_class("row-title")
            t_lbl.set_xalign(0.0)
            t_lbl.set_ellipsize(Pango.EllipsizeMode.END)
            t_lbl.set_max_width_chars(26)
            info_box.pack_start(t_lbl, False, False, 0)
            
            a_lbl = Gtk.Label(label=s["artist"])
            a_lbl.get_style_context().add_class("row-artist")
            a_lbl.set_xalign(0.0)
            a_lbl.set_ellipsize(Pango.EllipsizeMode.END)
            a_lbl.set_max_width_chars(26)
            info_box.pack_start(a_lbl, False, False, 0)
            box.pack_start(info_box, True, True, 0)
            
            if s.get("is_offline"):
                off_lbl = Gtk.Label(label="󰋋")
                off_lbl.get_style_context().add_class("status-badge")
                box.pack_start(off_lbl, False, False, 2)
            else:
                dl_btn = Gtk.Button(label="󰇚")
                dl_btn.get_style_context().add_class("action-opt-btn")
                dl_btn.set_tooltip_text("Download for offline")
                dl_btn.connect("clicked", lambda b, song=s: self.download_song(song))
                box.pack_start(dl_btn, False, False, 0)
                
            dur_min = s["duration"] // 60
            dur_sec = s["duration"] % 60
            dur_lbl = Gtk.Label(label=f"{dur_min:02d}:{dur_sec:02d}")
            dur_lbl.get_style_context().add_class("time-label")
            box.pack_start(dur_lbl, False, False, 2)
            
            row.add(box)
            self.list_queue.add(row)
            
        self.list_queue.show_all()
        self.set_status()
        
        if self.current_index == -1 and songs:
            self.load_song_index(0, auto_play=False)

    def on_queue_row_activated(self, listbox, row):
        idx = row.get_index()
        if 0 <= idx < len(self.playlist):
            self.load_song_index(idx, auto_play=True)

    # -------------------------------------------------------------------------
    # LIKE / FAVORITE SYSTEM
    # -------------------------------------------------------------------------
    def is_current_song_liked(self):
        if self.current_index == -1 or not self.playlist:
            return False
        cur = self.playlist[self.current_index]
        return any(s.get("id") == cur.get("id") or s.get("title") == cur.get("title") for s in self.liked_songs)

    def on_like_toggle(self, widget):
        if self.current_index == -1 or not self.playlist:
            return
        cur = self.playlist[self.current_index]
        
        existing = [s for s in self.liked_songs if s.get("id") == cur.get("id") or s.get("title") == cur.get("title")]
        if existing:
            self.liked_songs = [s for s in self.liked_songs if s.get("id") != cur.get("id") and s.get("title") != cur.get("title")]
            self.btn_like.set_label("󰣐 Like")
            self.btn_ov_like.set_label("󰣐 Like")
            self.btn_like.get_style_context().remove_class("btn-liked-active")
        else:
            self.liked_songs.insert(0, cur)
            self.btn_like.set_label("󰣐 Liked")
            self.btn_ov_like.set_label("󰣐 Liked")
            self.btn_like.get_style_context().add_class("btn-liked-active")
            
        save_liked_songs(self.liked_songs)
        self.btn_liked_list.set_label(f"󰋑 Liked ({len(self.liked_songs)})")

    def show_liked_playlist(self, widget):
        self.view_mode = "liked"
        self.btn_liked_list.get_style_context().add_class("btn-liked-active")
        self.btn_offline.get_style_context().remove_class("btn-offline-active")
        self.populate_playlist(self.liked_songs, "Liked Songs")

    # -------------------------------------------------------------------------
    # OFFLINE DOWNLOAD ENGINE
    # -------------------------------------------------------------------------
    def on_download_current(self, widget):
        if self.current_index == -1 or not self.playlist:
            return
        self.download_song(self.playlist[self.current_index])

    def download_song(self, song):
        song_id = song.get("id") or song.get("title")
        if song_id in self.downloading_ids:
            return
            
        self.downloading_ids.add(song_id)
        self.set_status("● DOWNLOADING...", "busy")
        
        def _dl():
            try:
                stream_url = song.get("stream_url")
                if not stream_url and song.get("encrypted_media_url"):
                    stream_url = decrypt_saavn_url(song.get("encrypted_media_url"))
                    
                if not stream_url:
                    GLib.idle_add(self.set_status, "● DL FAILED", "offline")
                    return
                    
                clean_title = re.sub(r'[\\/*?:"<>|]', "", song.get("title", "Song"))
                out_path = os.path.join(MUSIC_DIR, f"{clean_title}.mp4")
                
                req = urllib.request.Request(stream_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=15) as resp, open(out_path, "wb") as out_f:
                    while True:
                        chunk = resp.read(65536)
                        if not chunk:
                            break
                        out_f.write(chunk)
                        
                meta_path = os.path.join(MUSIC_DIR, f"{clean_title}.json")
                with open(meta_path, "w") as mf:
                    song_copy = dict(song)
                    song_copy["local_file"] = out_path
                    song_copy["is_offline"] = True
                    json.dump(song_copy, mf)
                    
                GLib.idle_add(self.set_status, "● DOWNLOADED", "online")
                GLib.idle_add(self.btn_download.set_label, "󰄬 Offline Saved")
            except Exception as e:
                print(f"[MusicPlayer] Download error: {e}")
                GLib.idle_add(self.set_status, "● DL ERROR", "offline")
            finally:
                self.downloading_ids.discard(song_id)
                GLib.timeout_add(2500, lambda: self.set_status() or False)
                
        threading.Thread(target=_dl, daemon=True).start()

    def show_offline_library(self, widget):
        self.view_mode = "offline"
        self.btn_offline.get_style_context().add_class("btn-offline-active")
        self.btn_liked_list.get_style_context().remove_class("btn-liked-active")
        
        offline_songs = []
        for f in os.listdir(MUSIC_DIR):
            if f.endswith(".json"):
                try:
                    with open(os.path.join(MUSIC_DIR, f), "r") as mf:
                        s = json.load(mf)
                        if os.path.exists(s.get("local_file", "")):
                            s["stream_url"] = f"file://{s['local_file']}"
                            offline_songs.append(s)
                except Exception:
                    pass
                    
        self.populate_playlist(offline_songs, "Offline Library")

    # -------------------------------------------------------------------------
    # PLAYBACK ENGINE & GSTREAMER
    # -------------------------------------------------------------------------
    def load_song_index(self, index, auto_play=True):
        if not (0 <= index < len(self.playlist)):
            return
            
        self.current_index = index
        song = self.playlist[index]
        
        # Update Meta in Center and Hover Overlay
        self.lbl_center_title.set_text(song["title"])
        self.lbl_center_artist.set_text(f"{song['artist']} • {song['album']}")
        
        self.lbl_ov_title.set_text(song["title"])
        self.lbl_ov_artist.set_text(song["artist"])
        self.lbl_ov_album.set_text(f"{song['album']} ({song['year']})" if song['album'] else "JioSaavn Single")
        self.lbl_ov_lang.set_text(song["language"] if song["language"] else "ORIGINAL")
        
        if self.is_current_song_liked():
            self.btn_like.set_label("󰣐 Liked")
            self.btn_ov_like.set_label("󰣐 Liked")
            self.btn_like.get_style_context().add_class("btn-liked-active")
        else:
            self.btn_like.set_label("󰣐 Like")
            self.btn_ov_like.set_label("󰣐 Like")
            self.btn_like.get_style_context().remove_class("btn-liked-active")
            
        dur_min = song["duration"] // 60
        dur_sec = song["duration"] % 60
        self.lbl_total_time.set_text(f"{dur_min:02d}:{dur_sec:02d}")
        self.progress_adj.set_upper(max(1, song["duration"]))
        self.progress_adj.set_value(0)
        self.lbl_curr_time.set_text("00:00")
        
        # Load Cover Art
        if song.get("image"):
            self.load_cover_art_from_url(song["image"])
        else:
            self.set_default_cover_art()
            
        row = self.list_queue.get_row_at_index(index)
        if row:
            self.list_queue.select_row(row)
            
        # Fetch Synced / Plain Lyrics
        threading.Thread(target=self.async_load_lyrics, args=(song,), daemon=True).start()
        
        self._fallback_url_idx = 0
        stream_url = song.get("stream_url")
        if stream_url:
            self.player.set_state(Gst.State.NULL)
            self.player.set_property("uri", stream_url)
            if auto_play:
                self.player.set_state(Gst.State.PLAYING)
                self.is_playing = True
                self.btn_play.set_label("󰏤")
            else:
                self.player.set_state(Gst.State.PAUSED)
                self.is_playing = False
                self.btn_play.set_label("󰐊")

    def async_load_lyrics(self, song):
        data = fetch_lyrics_data(song)
        GLib.idle_add(self.render_lyrics_ui, data)

    def render_lyrics_ui(self, data):
        self.current_lyrics = data
        self.current_lyric_idx = -1
        self.lyric_label_widgets = []
        
        for child in self.lyrics_container.get_children():
            self.lyrics_container.remove(child)
            
        lines = data.get("lines", [])
        for timestamp, text in lines:
            line_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            line_box.get_style_context().add_class("lyrics-line-box")
            
            lbl = Gtk.Label(label=text)
            lbl.get_style_context().add_class("lyrics-line-inactive")
            lbl.set_line_wrap(True)
            lbl.set_justify(Gtk.Justification.CENTER)
            lbl.set_xalign(0.5)
            
            line_box.pack_start(lbl, True, True, 0)
            self.lyrics_container.pack_start(line_box, False, False, 0)
            self.lyric_label_widgets.append((timestamp, lbl, line_box))
            
        self.lyrics_container.show_all()

    def update_synced_lyrics_highlight(self, current_sec):
        if not self.current_lyrics or not self.lyric_label_widgets:
            return
            
        lines = self.current_lyrics.get("lines", [])
        active_idx = -1
        for i, (ts, _) in enumerate(lines):
            if current_sec >= ts:
                active_idx = i
            else:
                break
                
        if active_idx != self.current_lyric_idx and active_idx != -1:
            self.current_lyric_idx = active_idx
            for idx, (_, lbl, box) in enumerate(self.lyric_label_widgets):
                if idx == active_idx:
                    lbl.get_style_context().remove_class("lyrics-line-inactive")
                    lbl.get_style_context().add_class("lyrics-line-active")
                    alloc = box.get_allocation()
                    adj = self.scroll_lyrics.get_vadjustment()
                    if alloc.height > 0:
                        target_v = max(0, alloc.y - 65)
                        adj.set_value(target_v)
                else:
                    lbl.get_style_context().remove_class("lyrics-line-active")
                    lbl.get_style_context().add_class("lyrics-line-inactive")

    def toggle_play_pause(self, widget=None):
        if self.current_index == -1 and self.playlist:
            self.load_song_index(0, auto_play=True)
            return
            
        if self.is_playing:
            self.player.set_state(Gst.State.PAUSED)
            self.is_playing = False
            self.btn_play.set_label("󰐊")
        else:
            self.player.set_state(Gst.State.PLAYING)
            self.is_playing = True
            self.btn_play.set_label("󰏤")

    def play_next(self, widget=None):
        if not self.playlist:
            return
            
        if self.repeat_mode == 2:
            self.load_song_index(self.current_index, auto_play=True)
            return
            
        if self.shuffle_mode:
            next_idx = random.randint(0, len(self.playlist) - 1)
        else:
            next_idx = self.current_index + 1
            if next_idx >= len(self.playlist):
                if self.repeat_mode == 1:
                    next_idx = 0
                else:
                    self.player.set_state(Gst.State.NULL)
                    self.is_playing = False
                    self.btn_play.set_label("󰐊")
                    return
                    
        self.load_song_index(next_idx, auto_play=True)

    def play_previous(self, widget=None):
        if not self.playlist:
            return
        prev_idx = self.current_index - 1
        if prev_idx < 0:
            prev_idx = len(self.playlist) - 1
        self.load_song_index(prev_idx, auto_play=True)

    def toggle_shuffle(self, widget):
        self.shuffle_mode = not self.shuffle_mode
        if self.shuffle_mode:
            self.btn_shuffle.get_style_context().add_class("btn-active")
        else:
            self.btn_shuffle.get_style_context().remove_class("btn-active")

    def toggle_repeat(self, widget):
        self.repeat_mode = (self.repeat_mode + 1) % 3
        if self.repeat_mode == 0:
            self.btn_repeat.set_label("󰑖")
            self.btn_repeat.get_style_context().remove_class("btn-active")
        elif self.repeat_mode == 1:
            self.btn_repeat.set_label("󰑖 All")
            self.btn_repeat.get_style_context().add_class("btn-active")
        else:
            self.btn_repeat.set_label("󰑘 1")
            self.btn_repeat.get_style_context().add_class("btn-active")

    def toggle_mute(self, widget):
        if self.volume > 0:
            self.prev_volume = self.volume
            self.vol_adj.set_value(0)
            self.btn_mute.set_label("󰝟")
        else:
            restored = getattr(self, "prev_volume", 0.85)
            self.vol_adj.set_value(restored * 100)
            self.btn_mute.set_label("󰕾")

    def on_volume_changed(self, scale):
        val = scale.get_value() / 100.0
        self.volume = val
        self.player.set_property("volume", val)
        self.lbl_vol_pct.set_text(f"{int(val*100)}%")
        if val == 0:
            self.btn_mute.set_label("󰝟")
        else:
            self.btn_mute.set_label("󰕾")

    # -------------------------------------------------------------------------
    # SEEKING & PROGRESS
    # -------------------------------------------------------------------------
    def on_seek_start(self, widget, event):
        self.is_seeking = True

    def on_seek_end(self, widget, event):
        self.is_seeking = False
        target_sec = self.progress_adj.get_value()
        self.player.seek_simple(
            Gst.Format.TIME,
            Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
            int(target_sec * Gst.SECOND)
        )

    def on_seek_change(self, scale, scroll_type, value):
        if self.is_seeking:
            cur_min = int(value) // 60
            cur_sec = int(value) % 60
            self.lbl_curr_time.set_text(f"{cur_min:02d}:{cur_sec:02d}")

    def update_playback_progress(self):
        if self.is_playing and not self.is_seeking:
            success, pos = self.player.query_position(Gst.Format.TIME)
            if success:
                pos_sec = pos / Gst.SECOND
                self.progress_adj.set_value(pos_sec)
                cur_min = int(pos_sec) // 60
                cur_sec = int(pos_sec) % 60
                self.lbl_curr_time.set_text(f"{cur_min:02d}:{cur_sec:02d}")
                self.update_synced_lyrics_highlight(pos_sec)
                
            success_dur, dur = self.player.query_duration(Gst.Format.TIME)
            if success_dur and dur > 0:
                dur_sec = dur / Gst.SECOND
                self.progress_adj.set_upper(dur_sec)
                d_min = int(dur_sec) // 60
                d_sec = int(dur_sec) % 60
                self.lbl_total_time.set_text(f"{d_min:02d}:{d_sec:02d}")
        return True

    def on_gst_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.EOS:
            self.play_next()
        elif t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            print(f"[MusicPlayer] GStreamer Error: {err}")
            self.check_network_async()
            if 0 <= self.current_index < len(self.playlist):
                cur_song = self.playlist[self.current_index]
                fallback_urls = cur_song.get("stream_urls", [])
                curr_try = getattr(self, "_fallback_url_idx", 0) + 1
                if curr_try < len(fallback_urls):
                    self._fallback_url_idx = curr_try
                    next_url = fallback_urls[curr_try]
                    print(f"[MusicPlayer] Retrying stream with fallback ({curr_try}): {next_url}")
                    self.player.set_state(Gst.State.NULL)
                    self.player.set_property("uri", next_url)
                    self.player.set_state(Gst.State.PLAYING)
                    return
            self._fallback_url_idx = 0
            self.play_next()

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_space and not self.search_entry.has_focus():
            self.toggle_play_pause()
            return True
        elif (event.keyval == Gdk.KEY_F5) or (event.keyval in (Gdk.KEY_r, Gdk.KEY_R) and (event.state & Gdk.ModifierType.CONTROL_MASK)):
            self.on_refresh_clicked()
            return True
        return False

    # -------------------------------------------------------------------------
    # DYNAMIC GEOMETRY DOCKING (Strictly matching combined left boxes height)
    # -------------------------------------------------------------------------
    def get_window_geometries(self):
        left_greeting = None
        sidebar_geom = None
        inputbox_geom = None
        try:
            out = subprocess.check_output(["xprop", "-root", "_NET_CLIENT_LIST"], stderr=subprocess.DEVNULL).decode()
            win_ids = [w.strip() for w in out.split("#")[1].split(",") if w.strip()]
            disp = Gdk.Display.get_default()
            
            for wid_str in win_ids:
                try:
                    prop = subprocess.check_output(["xprop", "-id", wid_str, "WM_CLASS"], stderr=subprocess.DEVNULL).decode()
                    wid = int(wid_str, 16)
                    xwin = GdkX11.X11Window.foreign_new_for_display(disp, wid)
                    if not xwin:
                        continue
                    _, ox, oy = xwin.get_origin()
                    _, _, w, h = xwin.get_geometry()
                    
                    if "ConkyGreeting" in prop:
                        left_greeting = (ox, oy, w, h)
                    elif "DesktopInputBox" in prop:
                        inputbox_geom = (ox, oy, w, h)
                    elif "Conky" in prop and "ConkyGreeting" not in prop:
                        if ox > 800:
                            sidebar_geom = (ox, oy, w, h)
                except Exception:
                    pass
        except Exception:
            pass
        return left_greeting, inputbox_geom, sidebar_geom

    def reposition_between_widgets(self):
        screen = self.get_screen()
        sw = screen.get_width()
        sh = screen.get_height()
        
        left_greeting, inputbox_geom, sidebar_geom = self.get_window_geometries()
        
        # Horizontal bounds
        if left_greeting:
            lx, ly, lw, lh = left_greeting
            start_x = lx + lw + 14
        elif inputbox_geom:
            ix, iy, iw, ih = inputbox_geom
            start_x = ix + iw + 14
        else:
            start_x = 490
            
        if sidebar_geom:
            rx, ry, rw, rh = sidebar_geom
            end_x = rx - 14
        else:
            end_x = sw - 290
            
        target_w = max(600, end_x - start_x)
        
        # Precise Combined Height of Left Input Box + Greeting Box
        if inputbox_geom and left_greeting:
            _, iy, _, _ = inputbox_geom
            _, ly, _, lh = left_greeting
            target_y = iy
            target_bottom = ly + lh
            target_h = max(280, target_bottom - target_y)
        elif left_greeting:
            _, ly, _, lh = left_greeting
            target_h = self.TARGET_HEIGHT
            target_y = (ly + lh) - target_h
        else:
            target_h = self.TARGET_HEIGHT
            target_y = sh - 325
            
        self.set_size_request(target_w, target_h)
        self.resize(target_w, target_h)
        self.move(start_x, target_y)

    def on_realize(self, widget):
        self.reposition_between_widgets()
        GLib.timeout_add(1000, self._periodic_snap_check, 0)

    def _periodic_snap_check(self, count):
        self.reposition_between_widgets()
        if count < 4:
            GLib.timeout_add(1500, self._periodic_snap_check, count + 1)
        return False


def main():
    app = DesktopMusicPlayer()
    app.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
