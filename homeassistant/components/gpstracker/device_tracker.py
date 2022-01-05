"""Platform for gpstracker.device_tracker integration."""
from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
import uuid

from gps_tracker import AsyncClient, Tracker
from gps_tracker.client.datatypes import TrackerStatus

from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=240)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the device_tracker platform."""

    client: AsyncClient = hass.data[DOMAIN].client
    trackers: list[Tracker] = await client.get_trackers()

    async_add_entities(
        [
            GpsTrackerEntity(client, tracker)
            for tracker in trackers
            if isinstance(tracker, Tracker)
        ],
        update_before_add=True,
    )


class GpsTrackerEntity(TrackerEntity):
    """Class for Invoxia™ GPS tracker devices."""

    def __init__(self, client: AsyncClient, tracker: Tracker) -> None:
        """Store tracker main properties."""
        super().__init__()

        # Static attributes
        self._client: AsyncClient = client
        self._tracker: Tracker = tracker

        _LOGGER.debug(f"Initializing Tracker {tracker.id}.")

        # Dynamic attributes
        self._available: bool = True

        self._battery: int | None = None

        self._latitude: float = 0.0
        self._longitude: float = 0.0
        self._accuracy: int = 0
        self._last_uuid: uuid.UUID = uuid.uuid4()

    async def _update_location(self) -> None:
        """Update tracker location."""
        locations = await self._client.get_locations(self._tracker, max_count=1)
        if locations[0].uuid != self._last_uuid:
            _LOGGER.debug(f"Location of Tracker {self._tracker.id} changed.")
            self._latitude = locations[0].lat
            self._longitude = locations[0].lng
            self._accuracy = locations[0].precision

    async def _update_battery(self) -> None:
        """Update tracker battery level."""
        tracker_status: TrackerStatus = await self._client.get_tracker_status(
            self._tracker
        )
        self._battery = tracker_status.battery

    async def async_update(self) -> None:
        """Update tracker data."""
        if not self.enabled:
            return
        _LOGGER.debug(f"Updating Tracker {self._tracker.id}.")
        await asyncio.gather(self._update_location(), self._update_battery())

    @property
    def should_poll(self) -> bool:
        """Indicate that trackers must be polled."""
        return True

    @property
    def unique_id(self) -> str | None:
        """Define tracker unique id."""
        return str(self._tracker.id)

    @property
    def name(self) -> str | None:
        """Define tracker name."""
        return self._tracker.name

    @property
    def location_accuracy(self) -> int:
        """Return accuration of last location data."""
        return self._accuracy

    @property
    def latitude(self) -> float | None:
        """Return last device latitude."""
        return self._latitude

    @property
    def longitude(self) -> float | None:
        """Return last device longitude."""
        return self._longitude

    @property
    def battery_level(self) -> int | None:
        """Return tracker battery level."""
        return self._battery

    @property
    def source_type(self) -> str:
        """Define source type as being GPS."""
        return "gps"
