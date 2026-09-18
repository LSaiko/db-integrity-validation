import pytest

from api.booking_client import BookingClient
from db.db_client import DbClient


@pytest.fixture(scope="session")
def api_client():
    return BookingClient()


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
