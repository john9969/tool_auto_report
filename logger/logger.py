import os
import threading
from datetime import datetime

class LoggerFactory:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                print("[LoggerFactory] Creating global singleton logger instance")
                cls._instance = super().__new__(cls)
            #else:
            #    print("[LoggerFactory] Reusing global logger instance")
            return cls._instance

    def add_log(self, log_type, content, tag="MyApp"):
        if log_type not in ["INFO", "BUG", "WARNING"]:
            raise ValueError("Invalid log type. Use INFO, BUG, or WARNING")

        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%Y-%m-%d %H:%M:%S")
        filename = f"logs/{date_str}.txt"
        os.makedirs("logs", exist_ok=True)

        def write():
            log_entry = f"[{time_str}] [{log_type}] [{tag}] {content}\r\n"
            #print(f"[LoggerFactory] Writing log to {filename}: {log_entry.strip()}")
            with open(filename, "a", encoding="utf-8") as file:
                file.write(log_entry)

        thread = threading.Thread(target=write)
        thread.start()
