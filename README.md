# db-integrity-validation

Tests that drive a booking API through its normal write path (create, update,
delete) and then verify the outcome directly in the Postgres database, plus a
few structural checks on the stored data itself.

## Quick start

```
docker compose -f db/docker-compose.yml up -d --build
pip install -r requirements.txt
pytest            # or: pytest -n auto (parallel-safe; each worker owns a block of room ids)
```

Every run writes `reports/report.html` (CI uploads it as an artifact).

The compose file starts Postgres on port 5433 (database, user and password are
all `bookings`) and a small Flask booking API on `http://localhost:5001/api`.

## Project layout

```
api/booking_client.py      BookingClient: create/update/delete via HTTP, payload() helper
db/db_client.py            DbClient: read-only psycopg access (get_booking_by_id, get_all_bookings)
db/docker-compose.yml      Postgres + Flask API
db/init.sql                bookings table + CHECK/EXCLUDE constraints, SELECT-only `reader` role
server/app.py, Dockerfile  stand-in Flask booking API (the system under test)
conftest.py                session-scoped api_client and db_client fixtures
tests/test_api_db_sync.py  API write -> DB read checks for create, update, delete
tests/test_negative_persistence.py  rejected requests leave the table untouched
tests/test_overlap.py      double-booking a room is a 409 and writes nothing
tests/test_boundary_values.py  unicode/long/quoted names round-trip exactly; blanks rejected
tests/test_concurrency.py  N parallel creates -> N rows; N racers for one slot -> 1 row
tests/test_schema.py       columns + named constraints match a frozen expectation
tests/test_data_integrity.py  NULL, uniqueness and date-ordering checks on all rows
```

## Why verify at the DB level

A 200 or 201 from the API only proves the handler returned successfully. It does
not prove the data was persisted, or persisted correctly. Things that a
response-only test will pass and a DB check will catch:

- A transaction that is silently rolled back after the response is built.
- Wrong column mapping, e.g. `firstname` and `lastname` swapped on insert.
- Dates truncated or shifted by a timezone conversion between the request and
  the `date` column.
- An update that inserts a new row instead of modifying the existing one.
- A soft delete that leaves the row in place while `GET` hides it.
- A response that echoes the request body rather than reading back the stored
  row, so the two can disagree without anyone noticing.

How the tests catch these:

- `test_api_db_sync.py` creates a booking through the API, then reads the row
  by id with `DbClient.get_booking_by_id` and compares every column to what was
  sent. Swapped names, shifted dates or a rolled-back insert all fail here
  regardless of what the API response said.
- The same file updates a booking and then checks both that the row with that
  id has the new values and that no extra row appeared, so an update that
  inserts instead of modifying is detected. After a delete it asserts the row
  is gone from the table, not just from the API.
- `test_data_integrity.py` scans every row for NULLs in required columns,
  duplicate ids, and `checkout_date > checkin_date`. These are cheap sanity
  checks that would surface a bad migration or a write path that stores
  incomplete data.

## Read-only DB access is deliberate

`DbClient` only issues `SELECT`s, and it connects as the `reader` role from
`init.sql`, which is granted SELECT only. So the restriction is enforced by
Postgres itself (`permission denied for table bookings`), not just by the
absence of a helper method. Writing to the database directly would bypass the
system under test: it would create state the API never produced, and it could
mask API-side bugs by making the table look right when the write path is
broken. All setup and teardown goes through the API so that every row the
tests observe came from the real write path, and every cleanup exercises the
real delete path.

## About the Flask API

The Flask service in `server/` is a stand-in for the real booking service. The
public restful-booker demo site exposes the same API shape, but its database
is not reachable, so there is nothing to verify against. The local API and
Postgres reproduce the relevant behaviour so the tests can check both sides.
