REQUIRED_COLUMNS = ("firstname", "lastname", "checkin_date", "checkout_date", "roomid")


def test_no_null_required_columns(db_client):
    for row in db_client.get_all_bookings():
        for col in REQUIRED_COLUMNS:
            assert row[col] is not None, f"row {row['id']} has NULL {col}"


def test_ids_are_unique(db_client):
    ids = [row["id"] for row in db_client.get_all_bookings()]
    assert len(ids) == len(set(ids))


def test_checkout_after_checkin(db_client):
    for row in db_client.get_all_bookings():
        assert row["checkout_date"] > row["checkin_date"], (
            f"row {row['id']}: checkout {row['checkout_date']} is not after checkin {row['checkin_date']}"
        )
