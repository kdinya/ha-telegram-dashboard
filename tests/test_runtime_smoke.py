"""Runtime smoke checks that do not require a full Home Assistant installation."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from aiohttp.test_utils import TestClient, TestServer
import yaml

from telegram_dashboard.src.config_manager import ConfigManager
from telegram_dashboard.src.renderer import MessageRenderer
from telegram_dashboard.src.web_server import WebApp


@pytest.mark.asyncio
async def test_ingress_http_routes_start_and_round_trip_config(tmp_path: Path):
    """Exercise the real aiohttp router, index, config and preview endpoints."""
    config_file = tmp_path / "config.json"
    manager = ConfigManager(config_file)
    manager.load()
    application = WebApp(manager, MessageRenderer()).app

    async with TestClient(TestServer(application)) as client:
        index = await client.get("/")
        assert index.status == 200
        assert "Telegram" in await index.text()

        config_response = await client.get("/api/config")
        assert config_response.status == 200
        config = await config_response.json()
        assert config["menu"]["main"]

        preview_response = await client.post(
            "/api/preview",
            json={"menu": config["menu"], "section_key": "main", "role": "admin"},
        )
        assert preview_response.status == 200
        preview = await preview_response.json()
        assert isinstance(preview["html"], str)
        assert isinstance(preview["keyboard"], list)


def test_companion_integration_copies_are_identical():
    """Prevent the packaged and repository companion copies from drifting."""
    source = Path("custom_components/telegram_dashboard")
    packaged = Path("telegram_dashboard/custom_components/telegram_dashboard")
    source_files = sorted(
        p.relative_to(source) for p in source.rglob("*") if p.is_file() and "__pycache__" not in p.parts
    )
    packaged_files = sorted(
        p.relative_to(packaged) for p in packaged.rglob("*") if p.is_file() and "__pycache__" not in p.parts
    )
    assert source_files == packaged_files
    for relative in source_files:
        source_digest = hashlib.sha256((source / relative).read_bytes()).hexdigest()
        packaged_digest = hashlib.sha256((packaged / relative).read_bytes()).hexdigest()
        assert source_digest == packaged_digest, f"companion copy drift: {relative}"


def test_companion_manifest_and_service_contract_are_json_loadable():
    """Validate the files consumed by Home Assistant before a runtime install."""
    manifest = json.loads(Path("custom_components/telegram_dashboard/manifest.json").read_text())
    services = yaml.safe_load(Path("custom_components/telegram_dashboard/services.yaml").read_text())
    assert manifest["domain"] == "telegram_dashboard"
    assert manifest["version"] == "1.1.3"
    assert {"send_message", "edit_message", "delete_message", "speak"} <= set(services)
