"""Double-booking a room must be rejected and must not leave a second row."""
import pytest

from api.booking_client import BookingClient

# booking fixture is room 1, 2027-05-01 -> 2027-05-03
OVERLAPS = {
    "same_dates": ("2027-05-01", "2027-05-03"),
    "starts_inside": ("2027-05-02", "2027-05-05"),
    "ends_inside": ("2027-04-29", "2027-05-02"),
    "surrounds": ("2027-04-29", "2027-05-05"),
}


@pytest.mark.parametrize("checkin,checkout", OVERLAPS.values(), ids=OVERLAPS.keys())
def test_overlapping_booking_rejected(api_client, booking, db_client, checkin, checkout):
    before = db_client.get_all_bookings()
    r = api_client.create_booking(BookingClient.payload(roomid=1, checkin=checkin, checkout=checkout))
    assert r.status_code == 409, r.text
    assert db_client.get_all_bookings() == before


@pytest.mark.parametrize("roomid,checkin,checkout", [
    (1, "2027-05-03", "2027-05-05"),  # checkout day == next checkin day: allowed (half-open range)
    (2, "2027-05-01", "2027-05-03"),  # same dates, different room
], ids=["back_to_back", "other_room"])
def test_adjacent_or_other_room_allowed(api_client, booking, db_client, roomid, checkin, checkout):
    r = api_client.create_booking(BookingClient.payload(roomid=roomid, checkin=checkin, checkout=checkout))
    assert r.status_code == 201, r.text
    assert db_client.get_booking_by_id(r.json()["bookingid"]) is not None
    api_client.delete_booking(r.json()["bookingid"])
