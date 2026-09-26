from pathlib import Path
from telegram_dashboard.src.config_manager import ConfigManager


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


def test_default_config_english_section_titles():
    from telegram_dashboard.src.config_manager import DEFAULT_CONFIG
    menu = DEFAULT_CONFIG["menu"]
    assert "Climate" in menu["climate"]["title"]
    assert "Water" in menu["water"]["title"]
    assert "Batteries" in menu["battery"]["title"]
    assert "System" in menu["system"]["title"]


def test_save_is_newline_terminated_and_backup_is_valid(tmp_path: Path):
    cfg_file = tmp_path / "config.json"
    cm = ConfigManager(cfg_file)
    cm.load()
    cm.save()
    first = cfg_file.read_bytes()
    assert first.endswith(b"\n")
    cm.upsert_user(55, "User", "guest")
    assert cfg_file.with_suffix(".json.bak").read_bytes() == first
    assert ConfigManager(cfg_file).load()["users"][0]["telegram_id"] == 55
