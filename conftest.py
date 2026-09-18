import time

import pytest
import requests

from api.booking_client import BookingClient
from db.db_client import DbClient


@pytest.fixture(scope="session")
def api_client():
    client = BookingClient()
    # ponytail: fixed 30s budget; enough for `docker compose up` to finish booting the API
    deadline = time.time() + 30
    while True:
        try:
            if client.get_booking(0).status_code == 404:  # any HTTP answer means the API is up
                return client
        except requests.ConnectionError:
            pass
        assert time.time() < deadline, f"API at {client.base_url} not reachable within 30s"
        time.sleep(1)


@pytest.fixture(scope="session")
def db_client():
    client = DbClient()
    yield client
    client.close()


@pytest.fixture
def booking(api_client):
    """Create a booking via the API; delete it after the test (via the API, never the DB)."""
    data = BookingClient.payload(firstname="Sync", lastname="Test")
    r = api_client.create_booking(data)
    assert r.status_code == 201, r.text
    data["bookingid"] = r.json()["bookingid"]
    yield data
    api_client.delete_booking(data["bookingid"])
