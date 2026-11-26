# Windows Auto Clicker

A small Tkinter utility for Windows. It supports left and right clicks, an F6 start/stop hotkey, and a configurable interval limited to 100–5000 ms (maximum 10 clicks per second). Clicking is off by default; move the pointer to the desired target and enable it deliberately.

## Run

1. Install Python 3 from [python.org](https://www.python.org/downloads/) (enable the option to add Python to PATH), or install it with `winget install Python.Python.3.12`.
2. Download or clone this repository and open PowerShell in its folder.
3. Run:

   ```powershell
   py -m pip install pynput
   py autoclicker.py
   ```

Press **F6** or use the window button to start/stop. Close the window to exit. If `pynput` is not installed, the on-screen button still works; install it to enable F6.
