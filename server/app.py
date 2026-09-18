"""Stand-in booking API (restful-booker endpoint shapes) backed by Postgres.

ponytail: exists only because the public demo site's DB is unreachable;
point BookingClient at the real service and drop this once one exists.
"""
import os
from datetime import date

import psycopg2
from psycopg2.errors import ExclusionViolation
from flask import Flask, abort, jsonify, request

app = Flask(__name__)


@app.errorhandler(ExclusionViolation)
def overlap(_):
    return jsonify(error="room already booked for those dates"), 409

conn = psycopg2.connect(os.environ["DATABASE_URL"])
conn.autocommit = True

COLS = "id, firstname, lastname, checkin_date, checkout_date, roomid"


def row_to_json(row):
    return {"bookingid": row[0], "firstname": row[1], "lastname": row[2],
            "bookingdates": {"checkin": row[3].isoformat(), "checkout": row[4].isoformat()},
            "roomid": row[5]}


def merge(body, row=None):
    """Request body over the existing row (partial PUT); returns validated column values or aborts 400."""
    cur = row_to_json(row) if row else {}
    d = {**cur.get("bookingdates", {}), **body.get("bookingdates", {})}
    v = {"firstname": body.get("firstname", cur.get("firstname")),
         "lastname": body.get("lastname", cur.get("lastname")),
         "checkin": d.get("checkin"), "checkout": d.get("checkout"),
         "roomid": body.get("roomid", cur.get("roomid"))}
    missing = [k for k, x in v.items() if x is None]
    if missing:
        abort(400, f"missing fields: {missing}")
    try:
        ci, co = date.fromisoformat(v["checkin"]), date.fromisoformat(v["checkout"])
    except (TypeError, ValueError):
        abort(400, "dates must be ISO YYYY-MM-DD")
    if co <= ci:
        abort(400, "checkout must be after checkin")
    return (v["firstname"], v["lastname"], ci, co, v["roomid"])


@app.post("/api/booking")
def create():
    with conn.cursor() as cur:
        cur.execute("INSERT INTO bookings (firstname, lastname, checkin_date, checkout_date, roomid) "
                    "VALUES (%s, %s, %s, %s, %s) RETURNING id", merge(request.json))
        return jsonify(bookingid=cur.fetchone()[0]), 201


@app.get("/api/booking/<int:bid>")
def get(bid):
    with conn.cursor() as cur:
        cur.execute(f"SELECT {COLS} FROM bookings WHERE id = %s", (bid,))
        row = cur.fetchone()
    return (jsonify(row_to_json(row)), 200) if row else ("", 404)


@app.put("/api/booking/<int:bid>")
def update(bid):
    with conn.cursor() as cur:
        cur.execute(f"SELECT {COLS} FROM bookings WHERE id = %s", (bid,))
        row = cur.fetchone()
        if not row:
            return "", 404
        cur.execute("UPDATE bookings SET firstname=%s, lastname=%s, checkin_date=%s, checkout_date=%s, roomid=%s "
                    "WHERE id = %s", merge(request.json, row) + (bid,))
        return jsonify(bookingid=bid), 200


@app.delete("/api/booking/<int:bid>")
def delete(bid):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM bookings WHERE id = %s", (bid,))
        return ("", 404) if cur.rowcount == 0 else ("", 202)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
