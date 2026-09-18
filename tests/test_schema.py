"""Frozen picture of the bookings table. A migration that renames, retypes or
drops a column the other tests never touch fails here, not in production."""

EXPECTED_COLUMNS = {
    "id": ("integer", "NO"),
    "firstname": ("text", "NO"),
    "lastname": ("text", "NO"),
    "checkin_date": ("date", "NO"),
    "checkout_date": ("date", "NO"),
    "roomid": ("integer", "NO"),
}
EXPECTED_CONSTRAINTS = {"bookings_pkey": "PRIMARY KEY", "checkout_after_checkin": "CHECK",
                        "names_not_blank": "CHECK", "no_double_booking": "EXCLUDE"}


def test_columns_match_frozen_schema(db_client):
    actual = {r["column_name"]: (r["data_type"], r["is_nullable"]) for r in db_client._select(
        "SELECT column_name, data_type, is_nullable FROM information_schema.columns "
        "WHERE table_name = 'bookings'")}
    assert actual == EXPECTED_COLUMNS


def test_constraints_present(db_client):
    actual = {r["conname"]: r["contype"] for r in db_client._select(
        "SELECT conname, CASE contype WHEN 'p' THEN 'PRIMARY KEY' WHEN 'c' THEN 'CHECK' "
        "WHEN 'x' THEN 'EXCLUDE' WHEN 'f' THEN 'FOREIGN KEY' WHEN 'u' THEN 'UNIQUE' END AS contype "
        "FROM pg_constraint WHERE conrelid = 'bookings'::regclass")}
    assert actual == EXPECTED_CONSTRAINTS
