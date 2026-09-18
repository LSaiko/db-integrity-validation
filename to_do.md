# To do

Ranked by value per line of code. Each item names the bug class it catches
(tests) or the constraint it removes (features). Skip anything that doesn't
map to a real defect or a real need.

## Tests — new bug classes

- [x] **Negative persistence**: API returns 4xx on invalid payload (missing
      field, checkout <= checkin, non-existent id) → assert row count unchanged.
      Catches "validation fails but the insert already happened".
- [x] **Partial update**: PUT with only some fields → assert untouched columns
      keep their old values. Catches "update wipes fields not in the body".
- [x] **Response vs. stored row**: compare `GET /booking/{id}` body to the DB
      row, not just the request to the DB. Catches "API echoes request, reads
      back something else".
- [x] **Delete idempotence** / [ ] orphans: DELETE twice → second is 404 and count
      unchanged. Once a second table exists (rooms, guests) → assert no
      booking references a missing parent (FK check via `LEFT JOIN … IS NULL`).
- [x] **Overlap constraint**: two bookings, same room, overlapping dates →
      API rejects, DB has one row. Only when the API claims to prevent it.
- [x] **Unicode / boundary values**: names with accents, apostrophes, 255+
      chars, whitespace-only → DB stores exactly what was sent (or API rejects).
- [x] **Concurrency**: N parallel creates (`concurrent.futures`) → N rows,
      N distinct ids. Catches non-atomic id generation or lost writes.
- [ ] **Property-based**: `hypothesis` strategy for payloads → create, read
      back from DB, compare. One test, many inputs. Add when hand-written
      boundary cases stop finding anything.

## Test infrastructure

- [ ] **DB assertion helper**: `assert_row_matches(row, payload)` already
      exists in test_api_db_sync.py; move to conftest once a second test file
      needs it, not before.
- [x] **Per-test isolation guard**: session-start snapshot of row count →
      session-end assert equal. Catches any test that leaks rows.
- [ ] **Schema drift check**: query `information_schema.columns` for
      `bookings` and compare to a frozen expected list. Catches a migration
      that silently renames/drops a column the tests never touch.
- [ ] **Parametrize `test_api_db_sync` over a few payload shapes** instead of
      one fixed `payload()`.
- [ ] **pytest-xdist**: verified NOT to work yet � the shared `booking` fixture
      uses a fixed room/dates, so parallel workers hit the overlap constraint.
      Fix: derive roomid from the worker id or a per-test counter; overlap
      tests must then read `booking["roomid"]` instead of assuming room 1.
- [x] **CI**: GitHub Actions job — `docker compose up -d --build`, `pytest`,
      `compose down -v`. Cache the pip install.
- [ ] **HTML/Allure report** on failure with the offending DB row dumped in
      the assertion message (already partly there via f-strings).

## Flexible features

- [ ] **Env-driven config**: `DATABASE_URL` and `API_URL` already read from
      env in one place each; add a single `config.py` only when a third
      setting appears.
- [ ] **Point at a real service**: document (README) exactly which two
      variables to set to run against a staging API + read replica, and
      delete `server/`. That was always the intent.
- [ ] **Schema migrations**: replace `init.sql` with the real service's
      migration tool once there is one; keep `init.sql` as the fallback for
      the stand-in.
- [ ] **Read-only role for the real DB**: the `reader` role pattern in
      `init.sql` is the thing to ask the DBA for on staging — SELECT-only
      credentials for the test runner, so the guarantee holds outside Docker.
- [ ] **Extra tables**: when rooms/guests exist, extend `DbClient` with
      `get_*` for each and add FK-orphan checks to `test_data_integrity.py`.
- [ ] **Wait for DB too**: `db_client` fixture currently assumes Postgres is
      up (compose healthcheck covers it); add the same retry loop as
      `api_client` if a non-compose environment ever needs it.
- [ ] **SQLAlchemy**: not needed. Two SELECTs don't justify an ORM. Revisit
      only if the query surface grows past ~10 methods.

## Known ceilings (ponytail: comments in code)

- `server/app.py` — stand-in API, single global connection, no validation.
  Fine for a test double; not a service.
- `conftest.py::api_client` — fixed 30s wait. Make it env-configurable if a
  slow CI runner needs more.
