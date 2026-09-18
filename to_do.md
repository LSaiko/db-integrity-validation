# To do

Ranked by value per line of code. Each item names the bug class it catches
(tests) or the constraint it removes (features). Skip anything that doesn't
map to a real defect or a real need.

**Status (2026-09-18): backlog drained.** 41 tests, CI green, xdist-safe.
Everything still open is blocked on pointing the suite at a real service.

## Done — and what each one caught

| Round | Item | Found on first run |
|---|---|---|
| 1 | sync tests: create/update/delete persist exactly | `conn.read_only = True` was a silent no-op under autocommit → replaced by a SELECT-only `reader` role |
| 2 | negative persistence (4xx leaves table untouched) | stand-in 500'd on missing fields, inserted checkout<=checkin |
| 2 | partial PUT keeps untouched columns | stand-in did full replace; "missing field" can't be an error on PUT |
| 2 | CI workflow | — |
| 3 | GET body == stored row | — |
| 3 | delete idempotent | — |
| 3 | room overlap → 409, one row | — (gist EXCLUDE from the start) |
| 4 | unicode / long / quoted names round-trip; blanks rejected | stand-in accepted `""` and `"   "` |
| 4 | 20 parallel creates; 20 racers for one slot → 1 row | — |
| 4 | session leak guard | the first blank-name test leaked a row |
| 5 | PUT into overlap → 409 not 500 | — |
| 5 | unique room per test | a fixture requested by both the test and `booking` is the *same* value (pytest caches per test) |
| 5 | xdist-safe | every before/after snapshot needed worker scoping, not just the leak guard |
| 6 | schema drift (columns + constraints frozen) | Postgres auto-names table CHECKs `bookings_check`, `_check1` → constraints now named |
| 6 | create parametrized over 5 date shapes (one-night, year-long, year boundary, leap day) | — |
| 6 | HTML report artifact; failures print the full stored row | pytest-html / pytest-xdist missing from requirements.txt (CI caught it) |
| 7 | `DB_URL` env override; DB wait loop | refused connect on Windows blocks 20s+/attempt → `connect_timeout=3` |
| 7 | README: running against a real service, what to ask the DBA for | — |

Two patterns:
- Every *data* defect was validation-before-write, and every fix landed as a
  DB constraint (CHECK / EXCLUDE) first, app-level 4xx second.
- Every *tooling* defect (no-op read_only, fixture caching, connect timeout,
  missing pins) was found by deliberately running the failure path, not by
  the green run. Keep doing that: break it on purpose, then fix.

## Blocked on a real service

Do these the day `API_URL` / `DB_URL` point at staging (README has the recipe):

- [ ] **Re-freeze `tests/test_schema.py`** to the real columns and constraint
      names. Expect this to be the first failure.
- [ ] **Prune stand-in-specific tests**: if the real API doesn't enforce
      overlap or blank names, delete `test_overlap.py` and the blank-name
      cases. Don't weaken them.
- [ ] **FK orphans**: once a second table exists (rooms, guests) → assert no
      booking references a missing parent (`LEFT JOIN … IS NULL`), and add
      `get_*` to `DbClient` for each table.
- [ ] **Schema migrations**: replace `init.sql` with the real service's
      migration tool; keep `init.sql` as the fallback for the stand-in.
- [ ] **Delete `server/`** and the compose `api` service.

## Deferred with a trigger

- [ ] **Property-based** (`hypothesis`): one create→read→compare test over a
      payload strategy. Trigger: a full round of hand-written cases finds
      nothing. Rounds 1–7 each found something, so not yet.
- [ ] **xdist in CI**: trigger: serial suite > 30s. Currently 1s; `-n 4`
      is 7× slower from worker startup.
- [ ] **`config.py`**: trigger: a third environment variable.
- [ ] **pydantic in `server/app.py::merge`**: trigger: a third nested object
      in the payload — or just delete the stand-in (see above).
- [ ] **Env-configurable wait budget** (`api_client` / `db_client` 30s):
      trigger: a CI runner that actually needs it.

## Won't do

- **SQLAlchemy** — two SELECTs and a schema query don't justify an ORM.
- **Move `assert_row_matches` to conftest** — one file uses it.
- **Allure** — pytest-html already produces the artifact.

## Known ceilings (`ponytail:` comments in code)

- `server/app.py` — single global psycopg2 connection shared across Flask
  threads. Survived 20 racers because of psycopg2's connection lock, not by
  design. Fine for a test double; not a service.
- `conftest.py` — 1000-room block per xdist worker; a single worker running
  more than 1000 room-consuming tests would wrap into the next block.
