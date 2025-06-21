import os, inspect
from colorama import Fore, Back, Style

COLOR_MAP = {

    # Foreground
    "fBlack": Fore.BLACK,
    "fRed": Fore.RED,
    "fGreen": Fore.GREEN,
    "fYellow": Fore.YELLOW,
    "fBlue": Fore.BLUE,
    "fMagenta": Fore.MAGENTA,
    "fCyan": Fore.CYAN,
    "fWhite": Fore.WHITE,

    # Background
    "bBlack": Back.BLACK,
    "bRed": Back.RED,
    "bGreen": Back.GREEN,
    "bYellow": Back.YELLOW,
    "bBlue": Back.BLUE,
    "bMagenta": Back.MAGENTA,
    "bCyan": Back.CYAN,
    "bWhite": Back.WHITE,
}

def get_caller_info():
    for frame_info in inspect.stack():
        filename = frame_info.filename
        if not filename.endswith("color_print.py"):
            short_name = os.path.basename(filename)
            return f"[{short_name}:{frame_info.lineno}]"
    return "[unknown]"

def custom_print(*args, color: str = None, bg: str = None, sep: str = " ", end: str = "\n", show_context = True):
    prefix = ""
    if color:
        prefix += COLOR_MAP.get(color, "")
    if bg:
        prefix += COLOR_MAP.get(bg, "")
        
    context = get_caller_info() if show_context else ""
    print(prefix + context, *args, Style.RESET_ALL, end=end)

# 🔵 INFO
def log_info(*args):
    custom_print("✅ [INFO]", *args, color="fGreen")

# 🟡 WARNING
def log_warn(*args):
    custom_print("⚠️ [WARN]", *args, color="fYellow")

# 🔴 ERROR
def log_error(*args):
    custom_print("❌ [ERROR]", *args, color="fRed", bg="bWhite")

# 🐞 DEBUG
def log_debug(*args):
    custom_print("🐞 [DEBUG]", *args, color="fCyan")
