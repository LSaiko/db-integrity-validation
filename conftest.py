import itertools
import os
import time

import pytest
import requests

from api.booking_client import BookingClient
from db.db_client import DbClient

# Each xdist worker (gw0, gw1, ...) owns a block of 1000 room ids so tests never
# collide on the overlap constraint; without xdist everything lives in 1000..1999.
WORKER = int(os.getenv("PYTEST_XDIST_WORKER", "gw0")[2:])
ROOM_BASE = 1000 * (WORKER + 1)
_rooms = itertools.count(ROOM_BASE)


@pytest.fixture
def roomid():
    """A room id no other test in this run will use."""
    return next(_rooms)


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


def mine(row):
    return ROOM_BASE <= row["roomid"] < ROOM_BASE + 1000


@pytest.fixture
def rows(db_client):
    """This worker's rows only, so before/after snapshots ignore other workers' in-flight writes."""
    return lambda: [r for r in db_client.get_all_bookings() if mine(r)]


@pytest.fixture(scope="session")
def db_client():
    client = DbClient()
    before = [r for r in client.get_all_bookings() if mine(r)]
    yield client
    leaked = [r for r in client.get_all_bookings() if mine(r) and r not in before]
    client.close()
    assert not leaked, f"tests leaked rows (a test wrote via the API without cleaning up): {leaked}"


@pytest.fixture
def booking(api_client):
    """Create a booking via the API; delete it after the test (via the API, never the DB).
    Draws its own room so a test's `roomid` fixture is always a different one."""
    data = BookingClient.payload(roomid=next(_rooms), firstname="Sync", lastname="Test")
    r = api_client.create_booking(data)
    assert r.status_code == 201, r.text
    data["bookingid"] = r.json()["bookingid"]
    yield data
    api_client.delete_booking(data["bookingid"])
