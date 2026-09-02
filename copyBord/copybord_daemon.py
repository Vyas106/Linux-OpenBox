#!/usr/bin/env python3
"""
copyBord Daemon - Auto Clipboard Monitor for Screenshots
Watches ~/Pictures/Screenshots/ for any newly saved screenshots and automatically copies
them to the X11 clipboard (xclip) so you can immediately paste (Ctrl+V) anywhere.
"""

import os
import sys
import time
import ctypes
import struct
import select
import subprocess
from pathlib import Path

SCREENSHOTS_DIR = Path.home() / "Pictures" / "Screenshots"
VALID_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}

# Linux inotify constants
IN_CLOSE_WRITE = 0x00000008
IN_MOVED_TO = 0x00000080
IN_CREATE = 0x00000100

libc = ctypes.CDLL("libc.so.6", use_errno=True)

def copy_to_clipboard(filepath: Path):
    """Copies image to X11 clipboard using xclip."""
    try:
        # Check that file exists and has non-zero size
        if not filepath.exists() or filepath.stat().st_size == 0:
            time.sleep(0.1) # brief wait if write is completing
            if not filepath.exists() or filepath.stat().st_size == 0:
                return

        # Copy to clipboard
        subprocess.run(
            ["xclip", "-selection", "clipboard", "-t", "image/png", "-i", str(filepath)],
            check=True,
            timeout=5
        )

        # Notify user
        subprocess.run(
            [
                "dunstify",
                "-a", "copyBord",
                "-i", str(filepath),
                "-u", "normal",
                "-t", "4000",
                "📋 Screenshot Copied to Clipboard",
                f"Ready to paste (Ctrl+V)\n{filepath.name}"
            ],
            check=False,
            timeout=5
        )
    except Exception as e:
        print(f"[copyBord] Error copying to clipboard: {e}", file=sys.stderr)

def watch_directory():
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Initialize inotify
    inotify_fd = libc.inotify_init()
    if inotify_fd < 0:
        errno = ctypes.get_errno()
        raise OSError(errno, f"inotify_init failed: {os.strerror(errno)}")

    mask = IN_CLOSE_WRITE | IN_MOVED_TO
    watch_fd = libc.inotify_add_watch(
        inotify_fd,
        str(SCREENSHOTS_DIR).encode('utf-8'),
        mask
    )
    if watch_fd < 0:
        errno = ctypes.get_errno()
        raise OSError(errno, f"inotify_add_watch failed: {os.strerror(errno)}")

    print(f"[copyBord] Monitoring {SCREENSHOTS_DIR} for screenshots...")
    
    poller = select.poll()
    poller.register(inotify_fd, select.POLLIN)

    # Struct format for inotify_event header: int wd, uint32 mask, uint32 cookie, uint32 len
    event_header_size = struct.calcsize("iIII")

    last_copied_file = None
    last_copied_time = 0

    try:
        while True:
            events = poller.poll()
            for fd, event in events:
                if fd == inotify_fd:
                    data = os.read(inotify_fd, 4096)
                    offset = 0
                    while offset + event_header_size <= len(data):
                        wd, mask_event, cookie, length = struct.unpack_from("iIII", data, offset)
                        offset += event_header_size
                        name_bytes = data[offset:offset + length]
                        offset += length
                        filename = name_bytes.rstrip(b'\x00').decode('utf-8', errors='ignore')
                        
                        if not filename:
                            continue

                        filepath = SCREENSHOTS_DIR / filename
                        if filepath.suffix.lower() in VALID_EXTENSIONS:
                            now = time.time()
                            # Debounce duplicate notifications within 1.0s for the same file
                            if str(filepath) == last_copied_file and (now - last_copied_time) < 1.0:
                                continue
                            
                            last_copied_file = str(filepath)
                            last_copied_time = now
                            copy_to_clipboard(filepath)
    except KeyboardInterrupt:
        pass
    finally:
        os.close(inotify_fd)

if __name__ == "__main__":
    watch_directory()
