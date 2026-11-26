"""A simple, user-controlled Windows mouse clicker.

Install and run:
    py -m pip install pynput
    py autoclicker.py

F6 toggles clicking. The interval is limited to 100–5000 ms (at most 10 CPS).
Close the window to stop the clicker.
"""

import ctypes
import threading
import tkinter as tk
from tkinter import messagebox, ttk

try:
    from pynput import keyboard
except ImportError:
    keyboard = None

if not hasattr(ctypes, "windll"):
    raise SystemExit("This utility is for Windows only.")

user32 = ctypes.windll.user32
INPUT_MOUSE = 0
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
ULONG_PTR = ctypes.c_size_t


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ULONG_PTR),
    ]


class INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("union",)
    _fields_ = [("type", ctypes.c_ulong), ("union", INPUT_UNION)]


def send_mouse_event(flags):
    event = INPUT(type=INPUT_MOUSE, mi=MOUSEINPUT(0, 0, 0, flags, 0, 0))
    if user32.SendInput(1, ctypes.byref(event), ctypes.sizeof(INPUT)) != 1:
        raise ctypes.WinError()


class ClickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple Clicker")
        self.root.resizable(False, False)
        self.running = threading.Event()
        self.stop_worker = threading.Event()
        self.config_lock = threading.Lock()
        self.click_button = "left"
        self.interval_ms = 500
        self.closing = False
        self.button_choice = tk.StringVar(value="left")
        self.status = tk.StringVar(value="Stopped — F6 to start")

        frame = ttk.Frame(root, padding=16)
        frame.grid()
        ttk.Label(frame, text="Mouse button:").grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(frame, text="Left", variable=self.button_choice, value="left", command=self._save_button).grid(row=1, column=0, sticky="w")
        ttk.Radiobutton(frame, text="Right", variable=self.button_choice, value="right", command=self._save_button).grid(row=1, column=1, sticky="w")

        ttk.Label(frame, text="Interval (100–5000 ms; max 10 clicks/sec):").grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(12, 0)
        )
        self.interval_slider = ttk.Scale(frame, from_=100, to=5000, orient="horizontal", command=self._save_interval)
        self.interval_slider.set(500)
        self.interval_slider.grid(row=3, column=0, columnspan=2, sticky="ew")
        self.interval_label = ttk.Label(frame, text="500 ms")
        self.interval_label.grid(row=4, column=0, columnspan=2)

        self.toggle_button = ttk.Button(frame, text="Start (F6)", command=self.toggle)
        self.toggle_button.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(12, 4))
        ttk.Label(frame, textvariable=self.status).grid(row=6, column=0, columnspan=2)
        ttk.Label(frame, text="F6 toggles. Close this window to stop.").grid(row=7, column=0, columnspan=2, pady=(8, 0))

        self.worker = threading.Thread(target=self._click_loop, daemon=True)
        self.worker.start()
        self.hotkey_listener = None
        if keyboard is not None:
            self.hotkey_listener = keyboard.GlobalHotKeys({"<f6>": self._hotkey_toggle})
            self.hotkey_listener.start()
        else:
            messagebox.showwarning(
                "Hotkey unavailable",
                "Install the hotkey dependency with:\npy -m pip install pynput\n\n"
                "You can still use the Start/Stop button.",
            )
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def _save_button(self):
        with self.config_lock:
            self.click_button = self.button_choice.get()

    def _save_interval(self, value):
        milliseconds = max(100, min(5000, int(float(value))))
        with self.config_lock:
            self.interval_ms = milliseconds
        self.interval_label.configure(text=f"{milliseconds} ms")

    def _hotkey_toggle(self):
        if not self.closing:
            self.root.after(0, self.toggle)

    def toggle(self):
        if self.running.is_set():
            self.running.clear()
            self.status.set("Stopped — F6 to start")
            self.toggle_button.configure(text="Start (F6)")
        else:
            self.running.set()
            self.status.set("Running — move pointer to target; F6 to stop")
            self.toggle_button.configure(text="Stop (F6)")

    def _click_loop(self):
        while not self.stop_worker.is_set():
            if not self.running.wait(timeout=0.1):
                continue
            if self.stop_worker.is_set() or not self.running.is_set():
                continue
            with self.config_lock:
                button = self.click_button
                interval = self.interval_ms / 1000.0
            down, up = (
                (MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP)
                if button == "left"
                else (MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP)
            )
            try:
                send_mouse_event(down)
                send_mouse_event(up)
            except OSError as exc:
                self.running.clear()
                if not self.closing:
                    self.root.after(0, lambda error=str(exc): self._show_click_error(error))
                continue
            # Enforce the selected interval, and allow window close to interrupt the wait.
            self.stop_worker.wait(interval)

    def _show_click_error(self, error):
        self.status.set("Stopped — click injection failed")
        self.toggle_button.configure(text="Start (F6)")
        messagebox.showerror("Clicker stopped", error)

    def close(self):
        self.closing = True
        self.running.clear()
        self.stop_worker.set()
        if self.hotkey_listener is not None:
            self.hotkey_listener.stop()
        self.root.destroy()


if __name__ == "__main__":
    window = tk.Tk()
    ClickerApp(window)
    window.mainloop()
