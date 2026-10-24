import os
import sys
from datetime import datetime

class DoctorLogger:
    def __init__(self, callback=None):
        self.callback = callback
        self.logs = []

    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] [{level}] {message}"
        self.logs.append(formatted)
        print(formatted, flush=True)
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
