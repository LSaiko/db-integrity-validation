import os

import psycopg
from psycopg.rows import dict_row


class DbClient:
    """Read-only view of the bookings table.

    Deliberately exposes only SELECTs: every write must go through the API so
    the tests verify the real persistence path rather than bypassing it.
    """

    def __init__(self, dsn=os.getenv("DB_URL", "postgresql://reader:reader@localhost:5433/bookings")):
        # `reader` role (see init.sql) has SELECT only: Postgres rejects writes, not just this class
        self.conn = psycopg.connect(dsn, autocommit=True, row_factory=dict_row, connect_timeout=3)

    def _select(self, sql, params=()):
        return self.conn.execute(sql, params).fetchall()

    def get_booking_by_id(self, booking_id):
        rows = self._select("SELECT * FROM bookings WHERE id = %s", (booking_id,))
        return rows[0] if rows else None

    def get_all_bookings(self):
        return self._select("SELECT * FROM bookings ORDER BY id")

    def close(self):
        self.conn.close()
