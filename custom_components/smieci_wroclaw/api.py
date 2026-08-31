"""Thin async client for the smieci.example.com HA API (/api/ha/v1/*).

Mirrors the routes in this repo's src/app/api/ha/v1/*: health, schedule, refresh. All three
require a PAT bearer token (created at /admin/tokeny on the website) — this path deliberately
bypasses Authelia (see deploy/traefik-dynamic-smieci.yml), so a bare, detail-free error on auth
failure is expected and not a bug.
"""

from __future__ import annotations

import asyncio

from aiohttp import ClientSession, ClientError

REQUEST_TIMEOUT = 15


class SmieciApiError(Exception):
    """Raised for any non-2xx response or transport failure."""


class SmieciAuthError(SmieciApiError):
    """Raised specifically for a 401 — the token is missing, wrong, or revoked."""


class SmieciClient:
    """Async client for one smieci.example.com instance."""

    def __init__(self, session: ClientSession, base_url: str, token: str) -> None:
        self._session = session
        self._base_url = base_url.rstrip("/")
        self._token = token

    async def _request(self, method: str, path: str) -> dict:
        url = f"{self._base_url}{path}"
        headers = {"Authorization": f"Bearer {self._token}"}
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                async with self._session.request(method, url, headers=headers) as resp:
                    if resp.status == 401:
                        raise SmieciAuthError("Token jest nieprawidlowy lub zostal odwolany.")
                    if resp.status >= 400:
                        text = await resp.text()
                        raise SmieciApiError(f"HTTP {resp.status}: {text[:200]}")
                    return await resp.json()
        except ClientError as err:
            raise SmieciApiError(f"Blad polaczenia z {url}: {err}") from err

    async def get_health(self) -> dict:
        return await self._request("GET", "/api/ha/v1/health")

    async def get_schedule(self) -> dict:
        return await self._request("GET", "/api/ha/v1/schedule")

    async def refresh(self) -> dict:
        return await self._request("POST", "/api/ha/v1/refresh")
