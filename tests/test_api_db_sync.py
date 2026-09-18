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


def test_update_persists_new_values_without_duplicate(api_client, booking, db_client, roomid, rows):
    before = len(rows())
    new = BookingClient.payload(roomid=roomid, checkin="2027-06-10", checkout="2027-06-12",
                                firstname="Updated", lastname="Person")
    r = api_client.update_booking(booking["bookingid"], new)
    assert r.status_code == 200, r.text

    assert_row_matches(db_client.get_booking_by_id(booking["bookingid"]), new)
    assert len(rows()) == before, "update must modify in place, not insert"


def test_delete_removes_row(api_client, booking, db_client):
    r = api_client.delete_booking(booking["bookingid"])
    assert r.status_code == 202, r.text
    assert db_client.get_booking_by_id(booking["bookingid"]) is None, "row still present after delete"


def test_partial_update_keeps_untouched_columns(api_client, booking, db_client):
    r = api_client.update_booking(booking["bookingid"], {"lastname": "Renamed"})
    assert r.status_code == 200, r.text

    row = db_client.get_booking_by_id(booking["bookingid"])
    assert row["lastname"] == "Renamed"
    assert_row_matches(row, {**booking, "lastname": "Renamed"})  # everything else unchanged


def test_api_response_matches_stored_row(api_client, booking, db_client):
    """The GET body must be read back from storage, not echoed from the request."""
    body = api_client.get_booking(booking["bookingid"]).json()
    row = db_client.get_booking_by_id(booking["bookingid"])
    assert body["bookingid"] == row["id"]
    assert_row_matches(row, body)


def test_delete_is_idempotent(api_client, booking, db_client, rows):
    assert api_client.delete_booking(booking["bookingid"]).status_code == 202
    before = rows()
    assert api_client.delete_booking(booking["bookingid"]).status_code == 404
    assert rows() == before
