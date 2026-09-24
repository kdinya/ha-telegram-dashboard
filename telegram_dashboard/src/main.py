"""Application entry point for Home Assistant Add-on container."""
import json
import logging
import os
import sys
from pathlib import Path

from .config_manager import ConfigManager
from .access_controller import AccessController
from .renderer import MessageRenderer
from .web_server import WebApp
from .ha_client import HAClient
from .bot_engine import BotEngine
from .telegram_bot import TelegramBotRunner

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("telegram_dashboard")


def load_options() -> dict:
    options_file = Path("/data/options.json")
    if options_file.exists():
        try:
            return json.loads(options_file.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning("Failed to parse /data/options.json: %s", e)
    return {}


def main() -> None:
    data_dir = Path("/data")
    config_path = data_dir / "config.json" if data_dir.exists() else Path("config.json")
    options = load_options()

    cm = ConfigManager(config_path)
    cm.load()
    renderer = MessageRenderer()
    access = AccessController(cm.config.get("users", []), default_role=cm.config.get("default_role", "guest"))

    supervisor_token = os.environ.get("SUPERVISOR_TOKEN", "")
    ha_client = None
    if supervisor_token:
        ha_client = HAClient("http://supervisor/core/api", supervisor_token)
        logger.info("Home Assistant API client configured via Supervisor")
    else:
        logger.warning("SUPERVISOR_TOKEN missing: HA catalog and service calls are disabled")

    # Wire up BotEngine
    async def ha_call_service(domain: str, service: str, target: dict | None = None):
        if ha_client:
            return await ha_client.call_service(domain, service, target)
        return None

    async def get_ha_state():
        if ha_client:
            return await ha_client.collect_dashboard_state({})
        return {}

    async def get_all_states():
        if not ha_client:
            return {}
        try:
            states = await ha_client.get_states()
            return {s.get("entity_id", ""): s.get("state", "") for s in states if "entity_id" in s}
        except Exception as e:
            logger.error("Error fetching states: %s", e)
            return {}

    bot_engine = BotEngine(
        config=cm.config,
        access_controller=access,
        renderer=renderer,
        ha_call_service=ha_call_service,
        get_ha_state=get_ha_state,
        get_all_states=get_all_states,
        config_manager=cm,
    )

    # Telegram token from options, env or config
    telegram_token = (
        options.get("telegram_token")
        or os.environ.get("TELEGRAM_TOKEN")
        or cm.config.get("telegram_token", "")
    )
    bot_runner = None
    if telegram_token:
        bot_runner = TelegramBotRunner(telegram_token, bot_engine, get_ha_state=get_ha_state)
        logger.info("Telegram Bot Runner configured with token")
    else:
        logger.info("Telegram token not provided yet; bot runner is idle")

    web_app = WebApp(cm, renderer, ha_client=ha_client, bot_engine=bot_engine)

    async def on_startup(app) -> None:
        if ha_client:
            try:
                catalog = await ha_client.collect_catalog()
                bot_engine.set_catalog(catalog)
                logger.info("Home Assistant catalog loaded into BotEngine")
            except Exception as e:
                logger.warning("Could not pre-load catalog: %s", e)
        if bot_runner:
            bot_runner.start()

    async def on_cleanup(app) -> None:
        if bot_runner:
            await bot_runner.stop()
        if ha_client is not None:
            await ha_client.close()

    web_app.app.on_startup.append(on_startup)
    web_app.app.on_cleanup.append(on_cleanup)

    port = int(os.environ.get("INGRESS_PORT", 8099))
    logger.info("Starting Telegram Dashboard Ingress Server on port %s...", port)
    from aiohttp import web
    web.run_app(web_app.app, port=port)


if __name__ == "__main__":
    main()
