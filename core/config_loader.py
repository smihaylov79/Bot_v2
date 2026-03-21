# core/config_loader.py

import yaml
import os


class ConfigLoader:
    def __init__(self, base_path="config"):
        self.base_path = base_path

    def load(self, filename):
        path = os.path.join(self.base_path, filename)

        if not os.path.exists(path):
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path, "r") as f:
            return yaml.safe_load(f)

    def load_all(self):
        return {
            "general": self.load("general.yaml"),
            "symbols": self.load("symbols.yaml"),
            "strategies": self.load("strategies.yaml"),
        }
