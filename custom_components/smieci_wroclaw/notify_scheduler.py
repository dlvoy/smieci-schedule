"""Registers/unregisters the per-target daily notification callbacks.

Each configured target (see const.py: TARGET_*) fires at a fixed local time and checks the
coordinator's latest data for fractions matching that target's event filter (jutro/dzisiaj) and
fraction filter, then calls the chosen notify entity/service with a Polish message.
"""

from __future__ import annotations

import logging
from datetime import date

from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.event import async_track_time_change

from .const import (
    DOMAIN,
    FRACTIONS,
    OPT_TARGETS,
    TARGET_ENABLED,
    TARGET_EVENTS,
    TARGET_FRACTIONS,
    TARGET_HOUR,
    TARGET_ID,
    TARGET_MINUTE,
    TARGET_NOTIFY_SERVICE,
)

_LOGGER = logging.getLogger(__name__)

_LABEL_BY_KEY = {f["key"]: f["label_pl"] for f in FRACTIONS}

_unsub_by_entry: dict[str, list] = {}


def _matching_fractions(schedule: dict, event: str, wanted_keys: list[str]) -> list[str]:
    """Fraction labels in `schedule` whose status matches `event` ('tomorrow' or 'today')."""
    labels: list[str] = []
    for fraction in schedule.get("fractions", []):
        if wanted_keys and fraction["key"] not in wanted_keys:
            continue
        if fraction.get("status") == event:
            labels.append(_LABEL_BY_KEY.get(fraction["key"], fraction["short_pl"]))
    return labels


def _compose_message(event: str, labels: list[str]) -> str:
    today_str = date.today().strftime("%d.%m")
    fractions_str = ", ".join(labels)
    if event == "today":
        return f"Dzisiaj ({today_str}) odbior odpadow: {fractions_str}. Wystaw pojemnik."
    return f"Jutro odbior odpadow: {fractions_str}. Wystaw pojemnik dzis wieczorem."


def _make_callback(hass: HomeAssistant, coordinator, target: dict):
    @callback
    def _fire(_now) -> None:
        hass.async_create_task(_async_fire(hass, coordinator, target))

    return _fire


async def _async_fire(hass: HomeAssistant, coordinator, target: dict) -> None:
    schedule = coordinator.data
    if not schedule:
        return

    wanted_fractions = target.get(TARGET_FRACTIONS) or []
    for event in target[TARGET_EVENTS]:
        labels = _matching_fractions(schedule, event, wanted_fractions)
        if not labels:
            continue
        message = _compose_message(event, labels)
        service = target[TARGET_NOTIFY_SERVICE]
        # An EntitySelector(domain="notify") gives an entity_id like "notify.mobile_app_phone";
        # calling it as a service (notify.<slug>) matches both that and legacy notify targets
        # configured directly as a service name.
        service_name = service.split(".", 1)[1] if service.startswith("notify.") else service
        try:
            await hass.services.async_call(
                "notify", service_name, {"message": message}, blocking=True
            )
        except Exception:  # noqa: BLE001 - one bad target must not break the others
            _LOGGER.exception("Nie udalo sie wyslac powiadomienia przez %s", service)


def async_setup_notifications(hass: HomeAssistant, entry: ConfigEntry, coordinator) -> None:
    targets = entry.options.get(OPT_TARGETS, [])
    unsubs = []

    for target in targets:
        if not target.get(TARGET_ENABLED, True):
            continue
        unsub = async_track_time_change(
            hass,
            _make_callback(hass, coordinator, target),
            hour=target[TARGET_HOUR],
            minute=target[TARGET_MINUTE],
            second=0,
        )
        unsubs.append(unsub)
        _LOGGER.debug(
            "Zarejestrowano cel powiadomien %s o %02d:%02d",
            target.get(TARGET_ID),
            target[TARGET_HOUR],
            target[TARGET_MINUTE],
        )

    _unsub_by_entry[entry.entry_id] = unsubs


def async_unload_notifications(hass: HomeAssistant, entry: ConfigEntry) -> None:
    for unsub in _unsub_by_entry.pop(entry.entry_id, []):
        unsub()
