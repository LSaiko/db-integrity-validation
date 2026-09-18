"""N parallel creates -> exactly N rows with N distinct ids (no lost writes, no id reuse)."""
from concurrent.futures import ThreadPoolExecutor

from api.booking_client import BookingClient
from conftest import ROOM_BASE

N = 20


def test_parallel_creates_all_persist(api_client, db_client, rows):
    before = {r["id"] for r in rows()}
    # distinct rooms per thread so the overlap constraint isn't what we're measuring
    payloads = [BookingClient.payload(roomid=ROOM_BASE + 900 + i, firstname=f"Thread{i}") for i in range(N)]
    with ThreadPoolExecutor(N) as pool:
        responses = list(pool.map(api_client.create_booking, payloads))
    ids = [r.json()["bookingid"] for r in responses]
    try:
        assert all(r.status_code == 201 for r in responses)
        assert len(set(ids)) == N
        after = {r["id"] for r in rows()}
        assert after - before == set(ids)
    finally:
        for i in ids:
            api_client.delete_booking(i)


def test_parallel_overlaps_yield_exactly_one_row(api_client, db_client, rows):
    """Same room, same dates, N racers: exactly one 201, the rest 409, one row."""
    before = len(rows())
    payloads = [BookingClient.payload(roomid=ROOM_BASE + 999, firstname=f"Racer{i}") for i in range(N)]
    with ThreadPoolExecutor(N) as pool:
        codes = [r.status_code for r in pool.map(api_client.create_booking, payloads)]
    try:
        assert sorted(codes) == [201] + [409] * (N - 1), codes
        assert len(rows()) == before + 1
    finally:
        for row in rows():
            if row["roomid"] == ROOM_BASE + 999:
                api_client.delete_booking(row["id"])
