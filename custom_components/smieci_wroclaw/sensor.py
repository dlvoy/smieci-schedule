"""Sensor entities: per-fraction date + status, plus overview sensors."""

from __future__ import annotations

from datetime import date, datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, FRACTIONS, STATUS_PL
from .entity import SmieciEntity, icon_url_for


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]

    entities: list[SensorEntity] = []
    for fraction in FRACTIONS:
        entities.append(FractionDateSensor(coordinator, entry.entry_id, fraction["key"], fraction["label_pl"]))
        entities.append(FractionStatusSensor(coordinator, entry.entry_id, fraction["key"], fraction["label_pl"]))

    entities.append(NextPickupSensor(coordinator, entry.entry_id))
    entities.append(ValidUntilSensor(coordinator, entry.entry_id))
    entities.append(LastUpdateSensor(coordinator, entry.entry_id))

    async_add_entities(entities)


def _fraction_data(coordinator, key: str) -> dict | None:
    for fraction in (coordinator.data or {}).get("fractions", []):
        if fraction["key"] == key:
            return fraction
    return None


class FractionDateSensor(SmieciEntity, SensorEntity):
    """Nearest pickup date for one fraction. device_class=date, empty when unknown."""

    _attr_device_class = SensorDeviceClass.DATE

    def __init__(self, coordinator, entry_id: str, key: str, label_pl: str) -> None:
        super().__init__(coordinator, entry_id)
        self._key = key
        self._attr_unique_id = f"{entry_id}_{key}_date"
        self._attr_name = label_pl

    @property
    def native_value(self) -> date | None:
        fraction = _fraction_data(self.coordinator, self._key)
        return _parse_date(fraction["next_date"]) if fraction else None

    @property
    def entity_picture(self) -> str | None:
        fraction = _fraction_data(self.coordinator, self._key)
        status = fraction["status"] if fraction else "unknown"
        return icon_url_for(self._key, status)

    @property
    def extra_state_attributes(self) -> dict:
        fraction = _fraction_data(self.coordinator, self._key)
        if not fraction:
            return {}
        return {
            "status": STATUS_PL.get(fraction["status"], fraction["status"]),
            "dni_do_odbioru": fraction["days_until"],
            "kolor": fraction["color"],
            "nastepne_terminy": fraction["upcoming"],
        }


class FractionStatusSensor(SmieciEntity, SensorEntity):
    """Enum status (nieznany/zaplanowany/jutro/dzisiaj) for one fraction."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = list(STATUS_PL.values())

    def __init__(self, coordinator, entry_id: str, key: str, label_pl: str) -> None:
        super().__init__(coordinator, entry_id)
        self._key = key
        self._attr_unique_id = f"{entry_id}_{key}_status"
        self._attr_name = f"{label_pl} — status"

    @property
    def native_value(self) -> str | None:
        fraction = _fraction_data(self.coordinator, self._key)
        if not fraction:
            return STATUS_PL["unknown"]
        return STATUS_PL.get(fraction["status"], STATUS_PL["unknown"])

    @property
    def entity_picture(self) -> str | None:
        fraction = _fraction_data(self.coordinator, self._key)
        status = fraction["status"] if fraction else "unknown"
        return icon_url_for(self._key, status)


class NextPickupSensor(SmieciEntity, SensorEntity):
    """Soonest pickup date across every fraction."""

    _attr_device_class = SensorDeviceClass.DATE
    _attr_name = "Najblizszy odbior"

    def __init__(self, coordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_next_pickup"

    @property
    def native_value(self) -> date | None:
        dates = [
            (f["next_date"], f["short_pl"])
            for f in (self.coordinator.data or {}).get("fractions", [])
            if f["next_date"]
        ]
        if not dates:
            return None
        dates.sort(key=lambda d: d[0])
        return _parse_date(dates[0][0])

    @property
    def extra_state_attributes(self) -> dict:
        fractions = (self.coordinator.data or {}).get("fractions", [])
        dated = [f for f in fractions if f["next_date"]]
        if not dated:
            return {}
        soonest = min(f["next_date"] for f in dated)
        which = [f["short_pl"] for f in dated if f["next_date"] == soonest]
        return {"frakcje": which}


class ValidUntilSensor(SmieciEntity, SensorEntity):
    """Last date covered by the currently known schedule."""

    _attr_device_class = SensorDeviceClass.DATE
    _attr_name = "Harmonogram wazny do"
    _attr_entity_category = "diagnostic"

    def __init__(self, coordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_valid_until"

    @property
    def native_value(self) -> date | None:
        return _parse_date((self.coordinator.data or {}).get("valid_until"))


class LastUpdateSensor(SmieciEntity, SensorEntity):
    """When smieci.example.com last successfully fetched the schedule."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_name = "Ostatnia aktualizacja"
    _attr_entity_category = "diagnostic"

    def __init__(self, coordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_last_update"

    @property
    def native_value(self) -> datetime | None:
        fetched_at = (self.coordinator.data or {}).get("fetched_at")
        if not fetched_at:
            return None
        return datetime.fromisoformat(fetched_at.replace("Z", "+00:00"))
