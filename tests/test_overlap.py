"""Double-booking a room must be rejected and must not leave a second row."""
import pytest

from api.booking_client import BookingClient

# booking fixture is 2027-05-01 -> 2027-05-03 in booking["roomid"]
OVERLAPS = {
    "same_dates": ("2027-05-01", "2027-05-03"),
    "starts_inside": ("2027-05-02", "2027-05-05"),
    "ends_inside": ("2027-04-29", "2027-05-02"),
    "surrounds": ("2027-04-29", "2027-05-05"),
}


@pytest.mark.parametrize("checkin,checkout", OVERLAPS.values(), ids=OVERLAPS.keys())
def test_overlapping_booking_rejected(api_client, booking, db_client, checkin, checkout, rows):
    before = rows()
    r = api_client.create_booking(BookingClient.payload(roomid=booking["roomid"], checkin=checkin, checkout=checkout))
    assert r.status_code == 409, r.text
    assert rows() == before


@pytest.mark.parametrize("same_room,checkin,checkout", [
    (True, "2027-05-03", "2027-05-05"),   # checkout day == next checkin day: allowed (half-open range)
    (False, "2027-05-01", "2027-05-03"),  # same dates, different room
], ids=["back_to_back", "other_room"])
def test_adjacent_or_other_room_allowed(api_client, booking, db_client, roomid, same_room, checkin, checkout):
    room = booking["roomid"] if same_room else roomid
    r = api_client.create_booking(BookingClient.payload(roomid=room, checkin=checkin, checkout=checkout))
    assert r.status_code == 201, r.text
    assert db_client.get_booking_by_id(r.json()["bookingid"]) is not None
    api_client.delete_booking(r.json()["bookingid"])


def test_update_into_overlap_rejected(api_client, booking, db_client, roomid):
    """The PUT path must map the constraint violation to 409, not 500, and change nothing."""
    other = api_client.create_booking(BookingClient.payload(roomid=roomid, checkin="2027-07-01", checkout="2027-07-03"))
    assert other.status_code == 201
    try:
        before = db_client.get_booking_by_id(booking["bookingid"])
        r = api_client.update_booking(booking["bookingid"], {"roomid": roomid, "bookingdates": {"checkin": "2027-07-02", "checkout": "2027-07-04"}})
        assert r.status_code == 409, r.text
        assert db_client.get_booking_by_id(booking["bookingid"]) == before
    finally:
        api_client.delete_booking(other.json()["bookingid"])
