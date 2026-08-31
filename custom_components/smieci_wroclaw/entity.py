"""Shared base entity: device info + the colored bin icon."""

from __future__ import annotations

from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN

# Matches __init__.py's ICONS_URL_PATH ("/api/smieci_wroclaw/icons").
_ICONS_URL_PATH = f"/api/{DOMAIN}/icons"


def icon_url_for(fraction_key: str, status: str) -> str:
    """entity_picture URL for a fraction's current status.

    Three drawn variants per fraction: outline (unknown/scheduled), filled (tomorrow), and
    filled+blinking (today, via an SVG <animate> — see icons/README in this directory).
    """
    variant = {"today": "blink", "tomorrow": "filled"}.get(status, "outline")
    return f"{_ICONS_URL_PATH}/{fraction_key}_{variant}.svg"


class SmieciEntity(CoordinatorEntity):
    """Base class giving every entity the same device grouping."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._entry_id = entry_id

    @property
    def device_info(self) -> DeviceInfo:
        address = (self.coordinator.data or {}).get("address") or {}
        street = address.get("street")
        house_number = address.get("house_number")
        label = f"{street} {house_number}" if street else "Harmonogram odpadow"
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=f"Smieci — {label}",
            manufacturer="smieci.example.com",
            model="Harmonogram wywozu odpadow",
        )
