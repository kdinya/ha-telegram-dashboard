"""Home Assistant API client used by the bot engine and the web UI."""
from __future__ import annotations

import json
from typing import Any

import aiohttp


class HAClient:
    """Thin async wrapper over the Home Assistant REST API."""

    def __init__(self, base_url: str, token: str, session: aiohttp.ClientSession | None = None) -> None:
        self._base = base_url.rstrip("/")
        self._token = token
        self._session = session or aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {token}"}
        )

    async def close(self) -> None:
        await self._session.close()

    async def _get(self, path: str) -> Any:
        async with self._session.get(f"{self._base}{path}") as resp:
            if resp.status != 200:
                text = await resp.text()
                raise RuntimeError(f"HA API {path} failed: {resp.status} {text[:200]}")
            return await resp.json()

    async def _post(self, path: str, payload: dict) -> Any:
        async with self._session.post(
            f"{self._base}{path}", data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
        ) as resp:
            if resp.status not in (200, 201):
                text = await resp.text()
                raise RuntimeError(f"HA API {path} failed: {resp.status} {text[:200]}")
            return await resp.json()

    async def get_state(self, entity_id: str) -> dict[str, Any] | None:
        return await self._get(f"/api/states/{entity_id}")

    async def get_states(self) -> list[dict[str, Any]]:
        return await self._get("/api/states")

    async def call_service(self, domain: str, service: str, target: dict | None = None) -> Any:
        payload: dict[str, Any] = {}
        if target:
            payload["target"] = target
        return await self._post(f"/api/services/{domain}/{service}", payload)

    async def render_template(self, template: str) -> Any:
        """Render a Jinja template through the HA REST API (/api/template)."""
        return await self._post("/api/template", {"template": template})

    async def collect_catalog(self) -> dict[str, Any]:
        """Collect the full entity catalog grouped by area, domain and label.

        Uses a single HA template for areas+domains (fast, one round trip).
        Labels are optional: on older HA versions the call fails and an
        empty mapping is returned instead of breaking the catalog.
        """
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
