"""Test the GPS Tracker device_tracker platform."""
from unittest.mock import patch
import uuid

from homeassistant.components.device_tracker.const import ATTR_SOURCE_TYPE
from homeassistant.components.gpstracker.const import DOMAIN
from homeassistant.const import (
    ATTR_BATTERY_LEVEL,
    ATTR_GPS_ACCURACY,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import TEST_CONF

from tests.common import MockConfigEntry


async def test_device_tracker_add_entities(
    hass: HomeAssistant, trackers, tracker_status, tracker_data
) -> None:
    """Test for device_tracker registration."""

    mock_config_entry = MockConfigEntry(
        domain=DOMAIN, data=TEST_CONF, unique_id=uuid.uuid4().hex
    )
    mock_config_entry.add_to_hass(hass)

    with patch(
        "gps_tracker.client.asynchronous.AsyncClient.get_trackers",
        return_value=trackers,
    ), patch(
        "gps_tracker.client.asynchronous.AsyncClient.get_tracker_status",
        return_value=tracker_status,
    ), patch(
        "gps_tracker.client.asynchronous.AsyncClient.get_locations",
        return_value=tracker_data,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    # Test entry properties
    entity_registry = er.async_get(hass)
    entry: er.RegistryEntry = entity_registry.async_get("device_tracker.dummy_tracker")
    assert entry
    assert entry.unique_id == "999999"

    # Test state
    state = hass.states.get("device_tracker.dummy_tracker")
    assert state
    assert state.attributes.get(ATTR_SOURCE_TYPE) == "gps"
    assert state.attributes.get(ATTR_BATTERY_LEVEL) == tracker_status.battery
    assert state.attributes.get(ATTR_GPS_ACCURACY) == tracker_data[0].precision
    assert state.attributes.get(ATTR_LATITUDE) == tracker_data[0].lat
    assert state.attributes.get(ATTR_LONGITUDE) == tracker_data[0].lng

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
