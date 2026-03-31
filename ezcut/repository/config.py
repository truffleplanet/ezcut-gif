from __future__ import annotations

import tomllib
from pathlib import Path

from ezcut.store.models import AppConfig

CONFIG_DIR = Path.home() / ".config" / "ezcut"
CONFIG_FILE = CONFIG_DIR / "config.toml"


class ConfigRepository:
    def __init__(self, config_file: Path = CONFIG_FILE) -> None:
        self.config_file = config_file
        self.config_dir = config_file.parent

    def load(self) -> AppConfig:
        if not self.config_file.exists():
            return AppConfig()

        with self.config_file.open("rb") as file:
            raw_config = tomllib.load(file)

        return AppConfig(
            mattermost_base_url=raw_config.get("mattermost", {}).get(
                "base_url", AppConfig.mattermost_base_url
            ),
            mattermost_add_path=raw_config.get("mattermost", {}).get(
                "add_path", AppConfig.mattermost_add_path
            ),
            mattermost_login_mode=raw_config.get("mattermost", {}).get(
                "login_mode", AppConfig.mattermost_login_mode
            ),
            chrome_user_data_dir=raw_config.get("chrome", {}).get(
                "user_data_dir", AppConfig.chrome_user_data_dir
            ),
            chrome_profile=raw_config.get("chrome", {}).get(
                "profile", AppConfig.chrome_profile
            ),
            default_tile_size=int(
                raw_config.get("split", {}).get(
                    "default_tile_size", AppConfig.default_tile_size
                )
            ),
            default_max_file_size_kb=int(
                raw_config.get("split", {}).get(
                    "default_max_file_size_kb",
                    AppConfig.default_max_file_size_kb,
                )
            ),
        )

    def save(self, config: AppConfig) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file.write_text(self._serialize(config), encoding="utf-8")

    def get(self, key: str) -> str:
        config = self.load()
        if not hasattr(config, key):
            raise KeyError(f"Unknown config key: {key}")
        return str(getattr(config, key))

    def set(self, key: str, value: str) -> None:
        config = self.load()
        if not hasattr(config, key):
            raise KeyError(f"Unknown config key: {key}")

        current_value = getattr(config, key)
        parsed_value = self._coerce_value(value, current_value)
        setattr(config, key, parsed_value)
        self.save(config)

    @staticmethod
    def _coerce_value(value: str, current_value: object) -> object:
        if isinstance(current_value, int):
            return int(value)
        return value

    @staticmethod
    def _serialize(config: AppConfig) -> str:
        return (
            "[mattermost]\n"
            f'base_url = "{config.mattermost_base_url}"\n'
            f'add_path = "{config.mattermost_add_path}"\n'
            f'login_mode = "{config.mattermost_login_mode}"\n\n'
            "[chrome]\n"
            f'user_data_dir = "{config.chrome_user_data_dir}"\n'
            f'profile = "{config.chrome_profile}"\n\n'
            "[split]\n"
            f"default_tile_size = {config.default_tile_size}\n"
            f"default_max_file_size_kb = {config.default_max_file_size_kb}\n"
        )
