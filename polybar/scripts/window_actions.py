#!/usr/bin/env python3
"""
Window Actions Utility for Openbox / X11
Handles:
- minimize_all / toggle_desktop
- close_all (gracefully closes all client windows)
"""

import sys
import ctypes
from ctypes import *

class XClientMessageEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', c_int),
        ('display', c_void_p),
        ('window', c_ulong),
        ('message_type', c_ulong),
        ('format', c_int),
        ('l', c_long * 5)
    ]

class XEvent(Union):
    _fields_ = [
        ('type', c_int),
        ('xclient', XClientMessageEvent),
        ('pad', c_long * 24)
    ]

try:
    x11 = CDLL('libX11.so.6')
    x11.XOpenDisplay.restype = c_void_p
    x11.XDefaultRootWindow.restype = c_ulong
    x11.XInternAtom.restype = c_ulong
    x11.XSendEvent.restype = c_int
    x11.XFlush.restype = c_int
    x11.XCloseDisplay.restype = c_int
    x11.XGetWindowProperty.restype = c_int
    x11.XFree.restype = c_int
except Exception as e:
    print(f"Error loading libX11: {e}", file=sys.stderr)
    sys.exit(1)

ClientMessage = 33
SubstructureNotifyMask = (1 << 19)
SubstructureRedirectMask = (1 << 20)

def send_client_message(display, root, window, message_type, data):
    event = XEvent()
    event.type = ClientMessage
    event.xclient.type = ClientMessage
    event.xclient.serial = 0
    event.xclient.send_event = 1
    event.xclient.display = display
    event.xclient.window = window
    event.xclient.message_type = message_type
    event.xclient.format = 32
    for i in range(min(5, len(data))):
        event.xclient.l[i] = data[i]
    
    mask = SubstructureNotifyMask | SubstructureRedirectMask
    x11.XSendEvent(display, root, False, mask, byref(event))
    x11.XFlush(display)

def get_root_property_atoms(display, root, prop_atom, req_type):
    actual_type_return = c_ulong()
    actual_format_return = c_int()
    nitems_return = c_ulong()
    bytes_after_return = c_ulong()
    prop_return = c_void_p()

    status = x11.XGetWindowProperty(
        display, root, prop_atom, 0, 1024, False,
        req_type,
        byref(actual_type_return),
        byref(actual_format_return),
        byref(nitems_return),
        byref(bytes_after_return),
        byref(prop_return)
    )

    if status == 0 and prop_return:
        count = nitems_return.value
        array_type = c_ulong * count
        result = list(array_type.from_address(prop_return))
        x11.XFree(prop_return)
        return result
    return []

def get_showing_desktop(display, root):
    atom_desktop = x11.XInternAtom(display, b'_NET_SHOWING_DESKTOP', False)
    atom_cardinal = x11.XInternAtom(display, b'CARDINAL', False)
    vals = get_root_property_atoms(display, root, atom_desktop, atom_cardinal)
    return vals[0] if vals else 0

def toggle_minimize_all():
    display = x11.XOpenDisplay(None)
    if not display:
        return
    root = x11.XDefaultRootWindow(display)
    atom_showing = x11.XInternAtom(display, b'_NET_SHOWING_DESKTOP', False)
    
    current = get_showing_desktop(display, root)
    new_state = 0 if current == 1 else 1
    send_client_message(display, root, root, atom_showing, [new_state, 0, 0, 0, 0])
    x11.XCloseDisplay(display)

def close_all():
    display = x11.XOpenDisplay(None)
    if not display:
        return
    root = x11.XDefaultRootWindow(display)
    atom_client_list = x11.XInternAtom(display, b'_NET_CLIENT_LIST', False)
    atom_window = x11.XInternAtom(display, b'WINDOW', False)
    atom_close = x11.XInternAtom(display, b'_NET_CLOSE_WINDOW', False)

    windows = get_root_property_atoms(display, root, atom_client_list, atom_window)
    for win in windows:
        send_client_message(display, root, win, atom_close, [0, 2, 0, 0, 0])

    x11.XCloseDisplay(display)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: window_actions.py [minimize_all|close_all]")
        sys.exit(1)
    
    cmd = sys.argv[1].lower()
    if cmd in ("minimize", "minimize_all", "toggle_desktop"):
        toggle_minimize_all()
    elif cmd in ("close", "close_all"):
        close_all()
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
