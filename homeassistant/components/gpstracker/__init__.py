"""The GPS Tracker integration."""
from __future__ import annotations

import attr as attrs
import gps_tracker

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from .const import DOMAIN

PLATFORMS: list[str] = ["device_tracker"]


@attrs.define(auto_attribs=True)
class GpsTrackerDomain:
    """Domain for gpstracker."""

    config: gps_tracker.Config
    client: gps_tracker.AsyncClient


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up GPS Tracker from a config entry."""
    config = gps_tracker.Config(  # type: ignore[call-arg]
        password=entry.data.get(CONF_PASSWORD),
        username=entry.data.get(CONF_USERNAME),
    )

    client = gps_tracker.AsyncClient(config)

    hass.data[DOMAIN] = GpsTrackerDomain(config=config, client=client)

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await hass.data[DOMAIN].client.close()

    return unload_ok
