import os
import sys
from datetime import datetime

# Enforce UTF-8 on Windows stdout/stderr to eliminate charmap/cp1253 UnicodeEncodeError
if sys.platform == "win32":
    try:
        if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

class DoctorLogger:
    def __init__(self, callback=None):
        self.callback = callback
        self.logs = []

    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] [{level}] {message}"
        self.logs.append(formatted)
        try:
            print(formatted, flush=True)
        except Exception:
            try:
                enc = getattr(sys.stdout, 'encoding', None) or 'ascii'
                safe_text = formatted.encode(enc, errors='replace').decode(enc)
                print(safe_text, flush=True)
            except Exception:
                pass

        if self.callback:
            try:
                self.callback(formatted)
            except Exception:
                pass

    def info(self, msg: str):
        self.log(msg, "INFO")

    def success(self, msg: str):
        self.log(msg, "SUCCESS")

    def warning(self, msg: str):
        self.log(msg, "WARNING")

    def error(self, msg: str):
        self.log(msg, "ERROR")

    def get_all_logs(self):
        return "\n".join(self.logs)
