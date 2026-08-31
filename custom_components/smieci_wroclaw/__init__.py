"""The smieci_wroclaw integration: waste-collection schedule from smieci.example.com."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SmieciClient
from .const import CONF_BASE_URL, CONF_TOKEN, DOMAIN
from .coordinator import SmieciCoordinator
from .notify_scheduler import async_setup_notifications, async_unload_notifications

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor", "button"]

ICONS_URL_PATH = f"/api/{DOMAIN}/icons"
ICONS_DIR = Path(__file__).parent / "icons"

_static_path_registered = False


async def _async_register_icons(hass: HomeAssistant) -> None:
    """Serve icons/*.svg locally so entity_picture works without reaching smieci.example.com."""
    global _static_path_registered
    if _static_path_registered:
        return

    from homeassistant.components.http import StaticPathConfig

    await hass.http.async_register_static_paths(
        [StaticPathConfig(ICONS_URL_PATH, str(ICONS_DIR), cache_headers=True)]
    )
    _static_path_registered = True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = async_get_clientsession(hass)
    client = SmieciClient(session, entry.data[CONF_BASE_URL], entry.data[CONF_TOKEN])
    coordinator = SmieciCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {"client": client, "coordinator": coordinator}

    await _async_register_icons(hass)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async_setup_notifications(hass, entry, coordinator)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Re-register notification-time callbacks after the options flow changes them."""
    async_unload_notifications(hass, entry)
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_setup_notifications(hass, entry, coordinator)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        async_unload_notifications(hass, entry)
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded
