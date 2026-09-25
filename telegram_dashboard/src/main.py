"""Application entry point for Home Assistant Add-on container."""
import json
import logging
import os
import re
import shutil
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


def get_ha_config_dir() -> Path | None:
    """Find the writable Home Assistant configuration directory (/homeassistant or /config)."""
    for p in [Path("/homeassistant"), Path("/config")]:
        if p.exists() and os.access(p, os.W_OK):
            return p
    return None


def sync_custom_component() -> None:
    """Sync companion integration into HA custom_components directory."""
    config_dir = get_ha_config_dir()
    if not config_dir:
        logger.warning("Home Assistant config directory (/homeassistant or /config) not found or not writable")
        return
    candidates = [
        Path("/app/custom_components/telegram_dashboard"),
        Path(__file__).resolve().parent.parent / "custom_components" / "telegram_dashboard",
        Path(__file__).resolve().parent.parent.parent / "custom_components" / "telegram_dashboard",
    ]
    source = None
    for cand in candidates:
        if cand.exists() and (cand / "manifest.json").exists():
            source = cand
            break
    if not source:
        logger.warning("Could not find telegram_dashboard companion integration source directory")
        return
    dest = config_dir / "custom_components" / "telegram_dashboard"
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, dest, dirs_exist_ok=True)
        logger.info("Successfully synced telegram_dashboard companion integration from %s to %s", source, dest)
    except Exception as e:
        logger.warning("Could not sync custom_component to %s: %s", dest, e)


def ensure_ha_integration_enabled() -> None:
    """Ensure 'telegram_dashboard:' is present in configuration.yaml if present."""
    config_dir = get_ha_config_dir()
    if not config_dir:
        return
    config_file = config_dir / "configuration.yaml"
    if not config_file.exists() or not os.access(config_file, os.W_OK):
        return
    try:
        cfg_content = config_file.read_text(encoding="utf-8")
        if re.search(r"^telegram_dashboard\s*:", cfg_content, flags=re.MULTILINE):
            return
        with open(config_file, "a", encoding="utf-8") as f:
            if cfg_content and not cfg_content.endswith("\n"):
                f.write("\n")
            f.write("\ntelegram_dashboard:\n")
        logger.info(
            "Added 'telegram_dashboard:' to %s. Restart Home Assistant to load the integration.",
            config_file
        )
    except Exception as e:
        logger.warning("Could not update %s: %s", config_file, e)


def main() -> None:
    data_dir = Path("/data")
    config_path = data_dir / "config.json" if data_dir.exists() else Path("config.json")
    options = load_options()

    # Sync custom component into HA /config if mounted
    sync_custom_component()
    ensure_ha_integration_enabled()

    cm = ConfigManager(config_path)
    cm.load()
    renderer = MessageRenderer()
    access = AccessController(cm.config.get("users", []), default_role=cm.config.get("default_role", "guest"))

    supervisor_token = os.environ.get("SUPERVISOR_TOKEN", "")
    ha_client = None
    if supervisor_token:
        ha_client = HAClient("http://supervisor/core", supervisor_token)
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
            try:
                states = await ha_client.get_states()
                res = {}
                for s in states:
                    eid = s.get("entity_id")
                    if eid:
                        res[eid] = {
                            "state": s.get("state"),
                            "attributes": s.get("attributes", {}),
                        }
                return res
            except Exception as e:
                logger.error("Error fetching states: %s", e)
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

    web_app = WebApp(
        cm,
        renderer,
        ha_client=ha_client,
        bot_engine=bot_engine,
        telegram_token=telegram_token,
        bot_runner=bot_runner,
    )

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
