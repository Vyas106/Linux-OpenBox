#!/usr/bin/env python3
"""
=============================================================================
Laptop & System Lock Screen Daemon
Handles:
  1. Laptop Lid Close / Sleep / Suspend (logind delay inhibitor & PrepareForSleep)
  2. Laptop Lock Key / loginctl lock-session (logind Session Lock signals)
  3. DBus org.freedesktop.ScreenSaver interface for apps & desktop tools
  4. Automatic Idle Screen Lock (X11 screen saver / inactivity monitor)
=============================================================================
"""

import os
import sys
import time
import signal
import ctypes
import subprocess
import threading
from gi.repository import Gio, GLib

LOCK_SCRIPT = os.path.expanduser("/home/vishal/Useless/lock.sh")
PID_FILE = os.path.expanduser("~/.cache/lock_daemon.pid")

# Idle timeout in seconds before auto-locking (default: 10 minutes = 600 seconds)
IDLE_TIMEOUT_SECONDS = int(os.environ.get("IDLE_LOCK_SECONDS", "600"))

# Ensure DISPLAY and XAUTHORITY are exported
os.environ.setdefault("DISPLAY", ":0")
if "XAUTHORITY" not in os.environ and os.path.exists(os.path.expanduser("~/.Xauthority")):
    os.environ["XAUTHORITY"] = os.path.expanduser("~/.Xauthority")

class XScreenSaverInfo(ctypes.Structure):
    _fields_ = [
        ('window', ctypes.c_ulong),
        ('state', ctypes.c_int),
        ('kind', ctypes.c_int),
        ('til_or_since', ctypes.c_ulong),
        ('idle', ctypes.c_ulong),
        ('eventMask', ctypes.c_ulong)
    ]

class LockDaemon:
    def __init__(self):
        self.inhibitor_fd = None
        self.system_bus = None
        self.session_bus = None
        self.is_locking = False
        self.x11 = None
        self.xss = None
        self.init_x11()

    def init_x11(self):
        try:
            self.x11 = ctypes.cdll.LoadLibrary("libX11.so.6")
            self.xss = ctypes.cdll.LoadLibrary("libXss.so.1")
            self.xss.XScreenSaverQueryInfo.argtypes = [
                ctypes.c_void_p,
                ctypes.c_ulong,
                ctypes.POINTER(XScreenSaverInfo)
            ]
            self.xss.XScreenSaverQueryInfo.restype = ctypes.c_int
        except Exception as e:
            print(f"[lock_daemon] X11/Xss library load warning: {e}", file=sys.stderr)

    def trigger_lock(self, wait_until_locked=False):
        """Launches the minimal lock screen."""
        if self.is_locking:
            return
        
        # Check if i3lock is already running
        try:
            res = subprocess.run(["pgrep", "-u", str(os.getuid()), "-x", "i3lock"],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if res.returncode == 0:
                return
        except Exception:
            pass

        self.is_locking = True
        try:
            env = os.environ.copy()
            if os.path.exists(LOCK_SCRIPT):
                subprocess.Popen(["bash", LOCK_SCRIPT], env=env)
            else:
                subprocess.Popen(["i3lock", "-c", "000000"], env=env)

            if wait_until_locked:
                # Wait briefly up to 1.5s for i3lock process to start
                for _ in range(15):
                    time.sleep(0.1)
                    res = subprocess.run(["pgrep", "-u", str(os.getuid()), "-x", "i3lock"],
                                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    if res.returncode == 0:
                        break
        except Exception as e:
            print(f"[lock_daemon] Error triggering lock: {e}", file=sys.stderr)
        finally:
            self.is_locking = False

    def take_sleep_inhibitor(self):
        """Requests a sleep delay inhibitor from systemd-logind."""
        if not self.system_bus:
            return
        try:
            # Release any previous inhibitor FD first
            self.release_sleep_inhibitor()

            res, out_fd_list = self.system_bus.call_with_unix_fd_list_sync(
                "org.freedesktop.login1",
                "/org/freedesktop/login1",
                "org.freedesktop.login1.Manager",
                "Inhibit",
                GLib.Variant("(ssss)", ("sleep", "LaptopLockDaemon", "Lock screen before sleep/lid close", "delay")),
                GLib.VariantType("(h)"),
                Gio.DBusCallFlags.NONE,
                -1,
                None,
                None
            )
            if out_fd_list and out_fd_list.get_length() > 0:
                self.inhibitor_fd = out_fd_list.get(0)
                print(f"[lock_daemon] Sleep inhibitor acquired (FD {self.inhibitor_fd})")
        except Exception as e:
            print(f"[lock_daemon] Could not acquire sleep inhibitor: {e}", file=sys.stderr)

    def release_sleep_inhibitor(self):
        """Closes the inhibitor FD to permit systemd to suspend."""
        if self.inhibitor_fd is not None:
            try:
                os.close(self.inhibitor_fd)
                print(f"[lock_daemon] Sleep inhibitor released (FD {self.inhibitor_fd})")
            except Exception as e:
                print(f"[lock_daemon] Error closing inhibitor FD: {e}", file=sys.stderr)
            self.inhibitor_fd = None

    def on_prepare_for_sleep(self, conn, sender, path, iface, signal, params, user_data):
        """Handles logind PrepareForSleep signal (before sleep and after resume)."""
        active = params.unpack()[0]
        if active:
            print("[lock_daemon] System preparing for sleep / lid close -> Locking screen...")
            # Lock screen and wait until i3lock is active
            self.trigger_lock(wait_until_locked=True)
            # Release inhibitor so systemd can proceed to suspend
            self.release_sleep_inhibitor()
        else:
            print("[lock_daemon] System resumed from sleep -> Re-acquiring sleep inhibitor...")
            # Re-acquire inhibitor for next sleep/lid close
            self.take_sleep_inhibitor()

    def on_session_lock(self, conn, sender, path, iface, signal, params, user_data):
        """Handles logind session Lock signal (loginctl lock-session)."""
        print("[lock_daemon] Logind session lock signal received -> Locking screen...")
        self.trigger_lock(wait_until_locked=False)

    def setup_session_dbus(self):
        """Registers org.freedesktop.ScreenSaver on session bus."""
        node_xml = """
        <node>
          <interface name="org.freedesktop.ScreenSaver">
            <method name="Lock"/>
            <method name="GetActive">
              <arg type="b" name="active" direction="out"/>
            </method>
            <method name="SetActive">
              <arg type="b" name="active" direction="in"/>
              <arg type="b" name="success" direction="out"/>
            </method>
          </interface>
        </node>
        """
        node_info = Gio.DBusNodeInfo.new_for_xml(node_xml).interfaces[0]

        def handle_method_call(conn, sender, path, iface, method, params, invocation):
            if method == "Lock":
                self.trigger_lock(wait_until_locked=False)
                invocation.return_value(None)
            elif method == "SetActive":
                active = params.unpack()[0]
                if active:
                    self.trigger_lock(wait_until_locked=False)
                invocation.return_value(GLib.Variant("(b)", (True,)))
            elif method == "GetActive":
                res = subprocess.run(["pgrep", "-u", str(os.getuid()), "-x", "i3lock"],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                is_active = (res.returncode == 0)
                invocation.return_value(GLib.Variant("(b)", (is_active,)))

        try:
            self.session_bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
            self.session_bus.register_object(
                "/org/freedesktop/ScreenSaver",
                node_info,
                handle_method_call,
                None,
                None
            )
            Gio.bus_own_name_on_connection(
                self.session_bus,
                "org.freedesktop.ScreenSaver",
                Gio.BusNameOwnerFlags.REPLACE,
                None,
                None
            )
            print("[lock_daemon] Registered org.freedesktop.ScreenSaver on session bus")
        except Exception as e:
            print(f"[lock_daemon] Session bus registration error: {e}", file=sys.stderr)

    def check_idle_timeout(self):
        """Checks X11 idle time and locks screen if timeout exceeded."""
        if not self.x11 or not self.xss or IDLE_TIMEOUT_SECONDS <= 0:
            return True

        try:
            display_str = os.environ.get("DISPLAY", ":0").encode("utf-8")
            display = self.x11.XOpenDisplay(display_str)
            if display:
                root = self.x11.XDefaultRootWindow(display)
                info = XScreenSaverInfo()
                res = self.xss.XScreenSaverQueryInfo(display, root, ctypes.byref(info))
                self.x11.XCloseDisplay(display)
                
                if res != 0:
                    idle_ms = info.idle
                    if idle_ms >= (IDLE_TIMEOUT_SECONDS * 1000):
                        print(f"[lock_daemon] Inactivity threshold reached ({idle_ms/1000:.1f}s) -> Locking screen...")
                        self.trigger_lock(wait_until_locked=False)
        except Exception as e:
            pass

        return True  # Keep GLib timeout alive

    def run(self):
        # Single instance PID check
        if os.path.exists(PID_FILE):
            try:
                with open(PID_FILE, "r") as f:
                    old_pid = int(f.read().strip())
                os.kill(old_pid, 0)
                print(f"[lock_daemon] Already running with PID {old_pid}. Exiting.")
                sys.exit(0)
            except (ProcessLookupError, ValueError):
                pass
            except PermissionError:
                sys.exit(0)

        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))

        # Register signals
        def cleanup(signum, frame):
            print("[lock_daemon] Shutting down...")
            self.release_sleep_inhibitor()
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
            sys.exit(0)

        signal.signal(signal.SIGINT, cleanup)
        signal.signal(signal.SIGTERM, cleanup)

        try:
            self.system_bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
            
            # Subscribe to logind PrepareForSleep (lid close, suspend)
            self.system_bus.signal_subscribe(
                "org.freedesktop.login1",
                "org.freedesktop.login1.Manager",
                "PrepareForSleep",
                "/org/freedesktop/login1",
                None,
                Gio.DBusSignalFlags.NONE,
                self.on_prepare_for_sleep,
                None
            )

            # Subscribe to logind Session Lock
            self.system_bus.signal_subscribe(
                "org.freedesktop.login1",
                "org.freedesktop.login1.Session",
                "Lock",
                None,
                None,
                Gio.DBusSignalFlags.NONE,
                self.on_session_lock,
                None
            )

            # Acquire sleep delay inhibitor
            self.take_sleep_inhibitor()

        except Exception as e:
            print(f"[lock_daemon] System bus error: {e}", file=sys.stderr)

        # Setup session bus ScreenSaver service
        self.setup_session_dbus()

        # Idle watcher timer every 15 seconds
        if IDLE_TIMEOUT_SECONDS > 0:
            GLib.timeout_add_seconds(15, self.check_idle_timeout)

        print("[lock_daemon] Lock daemon initialized and actively monitoring.")
        loop = GLib.MainLoop()
        try:
            loop.run()
        except KeyboardInterrupt:
            cleanup(None, None)

if __name__ == "__main__":
    daemon = LockDaemon()
    daemon.run()
