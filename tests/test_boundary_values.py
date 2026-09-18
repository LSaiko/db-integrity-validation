"""Awkward-but-valid values must round-trip through the API into the DB byte-for-byte."""
import pytest

from api.booking_client import BookingClient

NAMES = {
    "accents": "Zoë Ærø-Ñuñez",
    "apostrophe": "O'Brien",
    "cjk": "山田太郎",
    "emoji": "Test 🏨",
    "sql_ish": "Robert'); DROP TABLE bookings;--",
    "long_255": "x" * 255,
    "inner_whitespace": "Mary  Ann",
}


@pytest.mark.parametrize("name", NAMES.values(), ids=NAMES.keys())
def test_name_round_trips_exactly(api_client, db_client, roomid, name):
    r = api_client.create_booking(BookingClient.payload(roomid=roomid, firstname=name, lastname=name))
    assert r.status_code == 201, r.text
    bid = r.json()["bookingid"]
    try:
        row = db_client.get_booking_by_id(bid)
        assert (row["firstname"], row["lastname"]) == (name, name)
    finally:
        api_client.delete_booking(bid)


@pytest.mark.parametrize("name", ["", "   "], ids=["empty", "whitespace_only"])
def test_blank_name_rejected_and_not_stored(api_client, db_client, roomid, name, rows):
    before = rows()
    r = api_client.create_booking(BookingClient.payload(roomid=roomid, firstname=name))
    assert r.status_code == 400, r.text
    assert rows() == before
