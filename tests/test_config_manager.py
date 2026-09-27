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


def test_default_section_commands_presence_and_migration():
    from telegram_dashboard.src.config_manager import DEFAULT_SECTION_COMMANDS, ConfigManager
    import tempfile

    assert DEFAULT_SECTION_COMMANDS["main"] == "/start"
    assert DEFAULT_SECTION_COMMANDS["climate"] == "/climate"
    assert DEFAULT_SECTION_COMMANDS["light"] == "/light"
    assert DEFAULT_SECTION_COMMANDS["water"] == "/water"
    assert DEFAULT_SECTION_COMMANDS["battery"] == "/battery"
    assert DEFAULT_SECTION_COMMANDS["system"] == "/system"

    with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as f:
        # Simulate legacy config where default sections lacked 'command'
        legacy_cfg = (
            '{"version": "1.0.0", "menu": {"main": {"title": "Home", "roles": ["admin"]}, '
            '"climate": {"title": "Climate", "roles": ["admin"]}}, "users": []}'
        )
        f.write(legacy_cfg)
        f.flush()
        mgr = ConfigManager(f.name)
        cfg = mgr.load()
        assert cfg["menu"]["main"]["command"] == "/start"
        assert cfg["menu"]["climate"]["command"] == "/climate"


def test_validate_config_command_rules(tmp_path: Path):
    # Valid command format
    from telegram_dashboard.src.config_manager import validate_config, ConfigError
    cm = ConfigManager(tmp_path / "config.json")
    sample_config = cm.load()
    sample_config["menu"]["main"]["command"] = "/start"
    sample_config["menu"]["climate"]["command"] = "/climate"
    assert validate_config(sample_config) == sample_config

    # Invalid command characters or missing slash
    bad_cfg = dict(sample_config)
    bad_cfg["menu"] = dict(sample_config["menu"])
    bad_cfg["menu"]["custom"] = {"title": "Custom", "roles": ["admin"], "command": "invalid-no-slash"}
    import pytest
    with pytest.raises(ConfigError):
        validate_config(bad_cfg)

    # Duplicate command
    dup_cfg = dict(sample_config)
    dup_cfg["menu"] = dict(sample_config["menu"])
    dup_cfg["menu"]["custom"] = {"title": "Custom", "roles": ["admin"], "command": "/start"}
    with pytest.raises(ConfigError):
        validate_config(dup_cfg)
