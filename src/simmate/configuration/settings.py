# -*- coding: utf-8 -*-

# This the starting point provided by gpt

import os
import yaml

class Settings:
    def __init__(self):
        self.config = {}
        self.from_yaml()
        self.from_env()

    def load_from_yaml(self):
        yaml_path = os.path.expanduser("~/simmate/settings.yaml")
        if os.path.exists(yaml_path):
            with open(yaml_path, 'r') as f:
                self.config.update(yaml.safe_load(f))

    def load_from_env(self):
        for key, value in self.flatten_dict(self.config).items():
            env_key = f"SIMMATE__{key.upper().replace('.', '__')}"
            if env_key in os.environ:
                env_value = os.environ[env_key]
                if isinstance(value, bool):
                    self.config[key] = env_value.lower() == 'true'
                elif isinstance(value, int):
                    self.config[key] = int(env_value)
                else:
                    self.config[key] = env_value

    def flatten_dict(self, d, parent_key='', sep='.'):
        items = {}
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.update(self.flatten_dict(v, new_key, sep=sep))
            else:
                items[new_key] = v
        return items

    def get(self, key, default=None):
        return self.config.get(key, default)

# Usage example
settings = Settings()
database_engine = settings.get("database.ENGINE")
require_login = settings.get("website.require_login")
