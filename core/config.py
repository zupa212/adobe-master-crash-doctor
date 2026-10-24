import os
import json
from typing import Dict, Any

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")

DEFAULT_CONFIG = {
    "auto_gpu_override": True,
    "auto_junction": True,
    "clean_temp_files": True,
    "backup_preferences": True
}

class ConfigManager:
    def __init__(self, config_path: str = CONFIG_FILE):
        self.config_path = config_path
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Loads configuration from config.json."""
        cfg = DEFAULT_CONFIG.copy()
        if os.path.isfile(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    user_cfg = json.load(f)
                    cfg.update(user_cfg)
            except Exception:
                pass
        return cfg

    def save_config(self, updates: Dict[str, Any] = None) -> bool:
        """Saves current configuration to config.json."""
        if updates:
            self.config.update(updates)
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    def set(self, key: str, val: Any) -> bool:
        self.config[key] = val
        return self.save_config()
