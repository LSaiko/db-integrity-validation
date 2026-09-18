"""Rejected requests must leave the table untouched: validation that fires
after the write has already happened is the bug class here."""
import pytest

from api.booking_client import BookingClient

BAD_PAYLOADS = {
    "missing_lastname": {k: v for k, v in BookingClient.payload().items() if k != "lastname"},
    "checkout_before_checkin": BookingClient.payload(checkin="2027-05-03", checkout="2027-05-01"),
    "checkout_equals_checkin": BookingClient.payload(checkin="2027-05-01", checkout="2027-05-01"),
    "bad_date_format": BookingClient.payload(checkin="01/05/2027"),
}


@pytest.mark.parametrize("data", BAD_PAYLOADS.values(), ids=BAD_PAYLOADS.keys())
def test_invalid_create_writes_nothing(api_client, db_client, data):
    before = db_client.get_all_bookings()
    r = api_client.create_booking(data)
    assert 400 <= r.status_code < 500, r.text
    assert db_client.get_all_bookings() == before


# PUT is partial: a missing field is valid there, so only the date cases apply
BAD_UPDATES = {k: v for k, v in BAD_PAYLOADS.items() if k != "missing_lastname"}


@pytest.mark.parametrize("data", BAD_UPDATES.values(), ids=BAD_UPDATES.keys())
def test_invalid_update_changes_nothing(api_client, booking, db_client, data):
    before = db_client.get_booking_by_id(booking["bookingid"])
    r = api_client.update_booking(booking["bookingid"], data)
    assert 400 <= r.status_code < 500, r.text
    assert db_client.get_booking_by_id(booking["bookingid"]) == before


def test_update_and_delete_of_missing_id_write_nothing(api_client, db_client):
    before = db_client.get_all_bookings()
    assert api_client.update_booking(0, BookingClient.payload()).status_code == 404
    assert api_client.delete_booking(0).status_code == 404
    assert db_client.get_all_bookings() == before
