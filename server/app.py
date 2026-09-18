"""Stand-in booking API (restful-booker endpoint shapes) backed by Postgres.

ponytail: exists only because the public demo site's DB is unreachable;
point BookingClient at the real service and drop this once one exists.
"""
import os

import psycopg2
from flask import Flask, jsonify, request

app = Flask(__name__)
conn = psycopg2.connect(os.environ["DATABASE_URL"])
conn.autocommit = True

COLS = "id, firstname, lastname, checkin_date, checkout_date, roomid"


def row_to_json(row):
    return {"bookingid": row[0], "firstname": row[1], "lastname": row[2],
            "bookingdates": {"checkin": row[3].isoformat(), "checkout": row[4].isoformat()},
            "roomid": row[5]}


def values(body):
    d = body["bookingdates"]
    return (body["firstname"], body["lastname"], d["checkin"], d["checkout"], body["roomid"])


@app.post("/api/booking")
def create():
    with conn.cursor() as cur:
        cur.execute("INSERT INTO bookings (firstname, lastname, checkin_date, checkout_date, roomid) "
                    "VALUES (%s, %s, %s, %s, %s) RETURNING id", values(request.json))
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
        cur.execute("UPDATE bookings SET firstname=%s, lastname=%s, checkin_date=%s, checkout_date=%s, roomid=%s "
                    "WHERE id = %s", values(request.json) + (bid,))
        return ("", 404) if cur.rowcount == 0 else (jsonify(bookingid=bid), 200)


@app.delete("/api/booking/<int:bid>")
def delete(bid):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM bookings WHERE id = %s", (bid,))
        return ("", 404) if cur.rowcount == 0 else ("", 202)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
