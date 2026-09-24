from pathlib import Path
from telegram_dashboard.src.config_manager import ConfigManager, ConfigError
import pytest


def test_default_config_load(tmp_path: Path):
    cfg_file = tmp_path / "config.json"
    cm = ConfigManager(cfg_file)
    cfg = cm.load()
    assert "menu" in cfg
    assert "main" in cfg["menu"]
    assert cfg["version"] == "1.0.0"


def test_user_management(tmp_path: Path):
    cfg_file = tmp_path / "config.json"
    cm = ConfigManager(cfg_file)
    cm.load()
    cm.upsert_user(123456, "Dmytro", "admin")
    user = cm.get_user(123456)
    assert user is not None
    assert user["name"] == "Dmytro"
    assert user["role"] == "admin"

    deleted = cm.remove_user(123456)
    assert deleted is True
    assert cm.get_user(123456) is None
