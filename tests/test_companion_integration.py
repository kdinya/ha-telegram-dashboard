from pathlib import Path
import json
import yaml


def test_companion_manifest():
    manifest_file = Path("custom_components/telegram_dashboard/manifest.json")
    assert manifest_file.exists()
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert manifest["domain"] == "telegram_dashboard"
    assert manifest["version"] == "1.0.6"


def test_companion_services_yaml():
    services_file = Path("custom_components/telegram_dashboard/services.yaml")
    assert services_file.exists()
    services = yaml.safe_load(services_file.read_text(encoding="utf-8"))
    expected_services = [
        "send_message",
        "edit_message",
        "delete_message",
        "answer_callback",
        "send_photo",
        "send_document",
        "speak",
    ]
    for s in expected_services:
        assert s in services
        assert "description" in services[s]
        assert "fields" in services[s]
