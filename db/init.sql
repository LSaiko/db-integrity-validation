CREATE TABLE bookings (
    id            SERIAL PRIMARY KEY,
    firstname     TEXT    NOT NULL,
    lastname      TEXT    NOT NULL,
    checkin_date  DATE    NOT NULL,
    checkout_date DATE    NOT NULL,
    roomid        INTEGER NOT NULL
);
-- no seed rows: tests create their own data through the API

-- test-side role: SELECT only, so the DB itself rejects any write from db_client
CREATE ROLE reader LOGIN PASSWORD 'reader';
GRANT SELECT ON bookings TO reader;
