"""Application entry point for Home Assistant Add-on container."""
import asyncio
import logging
import os
import sys
from pathlib import Path

from .config_manager import ConfigManager
from .access_controller import AccessController
from .renderer import MessageRenderer
from .web_server import WebApp
from .ha_client import HAClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("telegram_dashboard")


def main() -> None:
    data_dir = Path("/data")
    config_path = data_dir / "config.json" if data_dir.exists() else Path("config.json")

    cm = ConfigManager(config_path)
    cm.load()
    renderer = MessageRenderer()
    supervisor_token = os.environ.get("SUPERVISOR_TOKEN", "")
    ha_client = None
    if supervisor_token:
        ha_client = HAClient("http://supervisor/core/api", supervisor_token)
        logger.info("Home Assistant API client configured via Supervisor")
    else:
        logger.warning("SUPERVISOR_TOKEN missing: HA catalog and service calls are disabled")
    web_app = WebApp(cm, renderer, ha_client=ha_client)

    port = int(os.environ.get("INGRESS_PORT", 8099))
    logger.info("Starting Telegram Dashboard Ingress Server on port %s...", port)
    from aiohttp import web
    web.run_app(web_app.app, port=port)


if __name__ == "__main__":
    main()
