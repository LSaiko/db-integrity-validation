from datetime import date

from api.booking_client import BookingClient


def assert_row_matches(row, data):
    assert row["firstname"] == data["firstname"]
    assert row["lastname"] == data["lastname"]
    assert row["roomid"] == data["roomid"]
    assert row["checkin_date"] == date.fromisoformat(data["bookingdates"]["checkin"])
    assert row["checkout_date"] == date.fromisoformat(data["bookingdates"]["checkout"])


def test_create_persists_exact_values(booking, db_client):
    row = db_client.get_booking_by_id(booking["bookingid"])
    assert row is not None, "API returned 201 but no row exists in the DB"
    assert_row_matches(row, booking)


def test_update_persists_new_values_without_duplicate(api_client, booking, db_client):
    before = len(db_client.get_all_bookings())
    new = BookingClient.payload(roomid=2, checkin="2027-06-10", checkout="2027-06-12",
                                firstname="Updated", lastname="Person")
    r = api_client.update_booking(booking["bookingid"], new)
    assert r.status_code == 200, r.text

    assert_row_matches(db_client.get_booking_by_id(booking["bookingid"]), new)
    assert len(db_client.get_all_bookings()) == before, "update must modify in place, not insert"


def test_delete_removes_row(api_client, booking, db_client):
    r = api_client.delete_booking(booking["bookingid"])
    assert r.status_code == 202, r.text
    assert db_client.get_booking_by_id(booking["bookingid"]) is None, "row still present after delete"
