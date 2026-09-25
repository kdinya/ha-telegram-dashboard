"""Home Assistant API client: REST and WebSocket clients for events and actions."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Callable, Awaitable

import aiohttp

logger = logging.getLogger("telegram_dashboard.ha_client")


class HAClient:
    """Async wrapper over Home Assistant REST and WebSocket APIs."""

    def __init__(self, base_url: str, token: str, session: aiohttp.ClientSession | None = None) -> None:
        self._base = base_url.rstrip("/")
        self._token = token
        self._session = session
        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._ws_task: asyncio.Task | None = None
        self._ws_running = False
        self._msg_id = 1
        self._subscriptions: dict[str, list[Callable[[dict[str, Any]], Awaitable[None]]]] = {}
        self._sub_id_to_event: dict[int, str] = {}

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Create the session lazily inside a running event loop."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={"Authorization": f"Bearer {self._token}"}
            )
        return self._session

    async def close(self) -> None:
        self._ws_running = False
        if self._ws_task and not self._ws_task.done():
            self._ws_task.cancel()
            try:
                await self._ws_task
            except (asyncio.CancelledError, Exception):
                pass
        if self._ws is not None and not self._ws.closed:
            await self._ws.close()
        if self._session is not None and not self._session.closed:
            await self._session.close()

    async def _get(self, path: str) -> Any:
        session = await self._ensure_session()
        async with session.get(f"{self._base}{path}") as resp:
            if resp.status != 200:
                text = await resp.text()
                raise RuntimeError(f"HA API {path} failed: {resp.status} {text[:200]}")
            return await resp.json()

    async def _post(self, path: str, payload: dict) -> Any:
        session = await self._ensure_session()
        async with session.post(
            f"{self._base}{path}", data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
        ) as resp:
            if resp.status not in (200, 201):
                text = await resp.text()
                raise RuntimeError(f"HA API {path} failed: {resp.status} {text[:200]}")
            return await resp.json()

    async def get_state(self, entity_id: str) -> dict[str, Any] | None:
        return await self._get(f"/api/states/{entity_id}")

    async def get_telegram_bot_name(self) -> str | None:
        """Return the title of a loaded Telegram bot config entry, without reading its credentials."""
        entries = await self._get("/api/config/config_entries/entry?domain=telegram_bot")
        if not isinstance(entries, list):
            return None
        return next(
            (
                entry["title"].strip()
                for entry in entries
                if isinstance(entry, dict)
                and entry.get("state") == "loaded"
                and isinstance(entry.get("title"), str)
                and entry["title"].strip()
            ),
            None,
        )

    async def get_states(self) -> list[dict[str, Any]]:
        return await self._get("/api/states")

    async def call_service(
        self,
        domain: str,
        service: str,
        target: dict | None = None,
        service_data: dict | None = None,
        return_response: bool = False,
    ) -> Any:
        payload: dict[str, Any] = {}
        if service_data:
            payload.update(service_data)
        if target:
            # Flatten target fields (entity_id, area_id, device_id) to top level for HA REST API
            for k, v in target.items():
                if isinstance(v, list) and len(v) == 1:
                    payload[k] = v[0]
                else:
                    payload[k] = v
        endpoint = f"/api/services/{domain}/{service}"
        if return_response:
            endpoint += "?return_response"
        return await self._post(endpoint, payload)

    async def render_template(self, template: str) -> Any:
        """Render a Jinja template through the HA REST API (/api/template)."""
        session = await self._ensure_session()
        async with session.post(
            f"{self._base}/api/template", data=json.dumps({"template": template}),
            headers={"Content-Type": "application/json"},
        ) as resp:
            if resp.status not in (200, 201):
                text = await resp.text()
                raise RuntimeError(f"HA API /api/template failed: {resp.status} {text[:200]}")
            raw_text = await resp.text()
            try:
                return json.loads(raw_text)
            except Exception:
                return raw_text

    async def collect_catalog(self) -> dict[str, Any]:
        """Collect the full entity catalog grouped by area, domain and label."""
        catalog: dict[str, Any] = {}
        core = (
            "{% set c = {'areas': {}, 'domains': {}} %}"
            "{% for a in areas() %}"
            "{% set _ = c['areas'].update({a: area_entities(a) | list}) %}"
            "{% endfor %}"
            "{% for grp in states | groupby('domain') %}"
            "{% set _ = c['domains'].update({grp[0]: grp[1] | map(attribute='entity_id') | list}) %}"
            "{% endfor %}"
            "{{ c | to_json }}"
        )
        core_result = await self.render_template(core)
        if isinstance(core_result, str):
            core_result = json.loads(core_result)
        catalog.update(core_result or {})
        try:
            labels_template = (
                "{% set c = {} %}"
                "{% for l in labels() %}"
                "{% set _ = c.update({l: label_entities(l) | list}) %}"
                "{% endfor %}"
                "{{ c | to_json }}"
            )
            labels_result = await self.render_template(labels_template)
            if isinstance(labels_result, str):
                labels_result = json.loads(labels_result)
            catalog["labels"] = labels_result or {}
        except RuntimeError:
            catalog["labels"] = {}
        return catalog

    async def collect_dashboard_state(self, entities: dict[str, list[str]]) -> dict[str, Any]:
        """Fetch a snapshot of states for entities referenced by the menu."""
        snapshot: dict[str, Any] = {}
        for entity_id in entities.get("sensors", []):
            state = await self.get_state(entity_id)
            snapshot[entity_id] = state.get("state") if state else None
        return snapshot

    # WebSocket event subscriptions
    def register_event_listener(
        self, event_type: str, callback: Callable[[dict[str, Any]], Awaitable[None]]
    ) -> None:
        """Register an async callback for a specific Home Assistant event type."""
        self._subscriptions.setdefault(event_type, []).append(callback)

    def _get_ws_url(self) -> str:
        if self._base.startswith("https://"):
            return "wss://" + self._base[8:] + "/websocket"
        if self._base.startswith("http://"):
            return "ws://" + self._base[7:] + "/websocket"
        return "ws://supervisor/core/websocket"

    def start_websocket(self) -> None:
        """Start background WebSocket connection loop to listen for HA events."""
        if self._ws_running:
            return
        self._ws_running = True
        self._ws_task = asyncio.create_task(self._ws_loop())

    async def _ws_loop(self) -> None:
        ws_url = self._get_ws_url()
        logger.info("Starting HA WebSocket client for %s...", ws_url)
        session = await self._ensure_session()

        while self._ws_running:
            try:
                async with session.ws_connect(ws_url) as ws:
                    self._ws = ws
                    # Step 1: Auth handshake
                    auth_req = await ws.receive_json()
                    if auth_req.get("type") != "auth_required":
                        logger.warning("Unexpected initial WS message: %s", auth_req)
                        await asyncio.sleep(2)
                        continue

                    await ws.send_json({"type": "auth", "access_token": self._token})
                    auth_resp = await ws.receive_json()
                    if auth_resp.get("type") != "auth_ok":
                        logger.error("HA WebSocket auth failed: %s", auth_resp)
                        await asyncio.sleep(5)
                        continue

                    logger.info("HA WebSocket authenticated successfully")
                    self._sub_id_to_event.clear()

                    # Step 2: Subscribe to all registered event types
                    for event_type in self._subscriptions.keys():
                        sub_id = self._msg_id
                        self._msg_id += 1
                        self._sub_id_to_event[sub_id] = event_type
                        await ws.send_json({
                            "id": sub_id,
                            "type": "subscribe_events",
                            "event_type": event_type,
                        })

                    # Step 3: Message receiving loop
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            if data.get("type") == "event":
                                event_payload = data.get("event", {})
                                event_type = event_payload.get("event_type")
                                if not event_type:
                                    sub_id = data.get("id")
                                    event_type = self._sub_id_to_event.get(sub_id)
                                callbacks = self._subscriptions.get(event_type or "", [])
                                for cb in callbacks:
                                    asyncio.create_task(cb(event_payload.get("data", {})))
                        elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                            break
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning("HA WebSocket connection dropped: %s. Reconnecting in 3s...", e)
                await asyncio.sleep(3)
