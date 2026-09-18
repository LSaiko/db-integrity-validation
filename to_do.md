# To do

Ranked by value per line of code. Each item names the bug class it catches
(tests) or the constraint it removes (features). Skip anything that doesn't
map to a real defect or a real need.

## Done (34 tests, CI green) — and what each one caught

| Test file | Bug class | Found on first run |
|---|---|---|
| test_api_db_sync | create/update/delete persist exactly; GET reads storage not request; delete idempotent | — |
| test_negative_persistence | 4xx must leave the table untouched | stand-in 500'd on missing fields, inserted checkout<=checkin |
| test_api_db_sync (partial PUT) | update wipes fields not in body | stand-in did full replace → now merges; "missing field" can't be an error on PUT |
| test_overlap | double-booking | — (built with gist EXCLUDE from the start) |
| test_boundary_values | unicode/long/quoted names round-trip; blanks rejected | stand-in accepted `""` and `"   "` |
| test_concurrency | lost writes; N racers for one slot → 1 row | — |
| conftest leak guard | any test leaving rows behind | the first blank-name test leaked a row |
| test_data_integrity | NULLs, dup ids, date order | — |

Pattern so far: every defect was in validation-before-write. Every fix landed
as a DB constraint (CHECK / EXCLUDE) first, app-level 4xx second.

## Tests — new bug classes

- [ ] **Update into overlap**: PUT that moves a booking onto another's dates →
      409, row unchanged. The EXCLUDE constraint covers it, but nothing proves
      the *update* path maps the violation to 409 rather than 500.
- [ ] **FK orphans**: once a second table exists (rooms, guests) → assert no
      booking references a missing parent (`LEFT JOIN … IS NULL`).
- [ ] **Property-based**: `hypothesis` strategy for payloads → create, read
      back from DB, compare. One test, many inputs. Still deferred: the
      hand-written boundary cases found two bugs last round.

## Test infrastructure

- [ ] **DB assertion helper**: `assert_row_matches(row, payload)` lives in
      test_api_db_sync.py; still only one file uses it. Leave it there.
- [ ] **Unique room per test** (unblocks xdist, and removes the hard-coded
      "room 1" the overlap tests assume): `booking` fixture takes roomid from
      an itertools counter seeded by worker id; overlap tests read
      `booking["roomid"]`.
- [ ] **Schema drift check**: query `information_schema.columns` for
      `bookings` and compare to a frozen expected list. Catches a migration
      that silently renames/drops a column the tests never touch.
- [ ] **Parametrize `test_api_db_sync` over a few payload shapes** instead of
      one fixed `payload()`.
- [ ] **pytest-xdist**: `-n auto` → 9 failed / 10 errors. Blocked on the
      unique-room item above; the leak guard also needs to be per-worker or
      it'll flag other workers' in-flight rows.
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

- `server/app.py` — stand-in API: single global psycopg2 connection, shared
  across Flask's threads. Held up under 20 concurrent racers, but that is
  psycopg2's connection-level lock doing the work, not design. Fine for a
  test double; not a service.
- `server/app.py::merge` — validation is a hand-rolled dict merge. Swap for
  pydantic if the payload grows a third nested object.
- `conftest.py::api_client` — fixed 30s wait. Make it env-configurable if a
  slow CI runner needs more.
