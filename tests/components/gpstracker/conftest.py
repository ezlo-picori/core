"""Fixtures for gpstracker integration tests."""
import json
from typing import List

from gps_tracker.client.datatypes import Device, Tracker, TrackerData, TrackerStatus
import pytest

from tests.common import load_fixture


@pytest.fixture
def trackers():
    """Form dummy data mocking client.get_trackers method."""
    data = json.loads(load_fixture("gpstracker/trackers.json"))
    trackers: List[Tracker] = []
    for item in data:
        device = Device.get(item)
        if isinstance(device, Tracker):
            trackers.append(device)
    return trackers


@pytest.fixture
def tracker_status():
    """Form dummy data mocking client.get_tracker_status method."""
    data = json.loads(load_fixture("gpstracker/tracker_status.json"))
    return TrackerStatus(**data)


@pytest.fixture
def tracker_data():
    """Form dummy data mocking client.get_locations method."""
    data = json.loads(load_fixture("gpstracker/tracker_data.json"))
    return [TrackerData(**item) for item in data]
