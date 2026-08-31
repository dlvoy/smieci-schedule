"""Binary sensors: per-fraction 'wystaw pojemnik' (on for tomorrow/today) + API connectivity."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, FRACTIONS
from .entity import SmieciEntity, icon_url_for


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities: list[BinarySensorEntity] = [
        FractionWystawSensor(coordinator, entry.entry_id, f["key"], f["label_pl"]) for f in FRACTIONS
    ]
    entities.append(ConnectivitySensor(coordinator, entry.entry_id))

    async_add_entities(entities)


def _fraction_data(coordinator, key: str) -> dict | None:
    for fraction in (coordinator.data or {}).get("fractions", []):
        if fraction["key"] == key:
            return fraction
    return None


class FractionWystawSensor(SmieciEntity, BinarySensorEntity):
    """On when a fraction is due tomorrow or today — what automations should key off."""

    def __init__(self, coordinator, entry_id: str, key: str, label_pl: str) -> None:
        super().__init__(coordinator, entry_id)
        self._key = key
        self._attr_unique_id = f"{entry_id}_{key}_wystaw"
        self._attr_name = f"{label_pl} — wystaw pojemnik"

    @property
    def is_on(self) -> bool:
        fraction = _fraction_data(self.coordinator, self._key)
        return bool(fraction and fraction["status"] in ("tomorrow", "today"))

    @property
    def entity_picture(self) -> str | None:
        fraction = _fraction_data(self.coordinator, self._key)
        status = fraction["status"] if fraction else "unknown"
        return icon_url_for(self._key, status)


class ConnectivitySensor(SmieciEntity, BinarySensorEntity):
    """On when the last poll of smieci.example.com succeeded."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_name = "Polaczenie z smieci.example.com"
    _attr_entity_category = "diagnostic"

    def __init__(self, coordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_connectivity"

    @property
    def is_on(self) -> bool:
        return self.coordinator.last_update_success
