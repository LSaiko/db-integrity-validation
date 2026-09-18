CREATE EXTENSION btree_gist;  -- for the no-overlap exclusion constraint below

CREATE TABLE bookings (
    id            SERIAL PRIMARY KEY,
    firstname     TEXT    NOT NULL,
    lastname      TEXT    NOT NULL,
    checkin_date  DATE    NOT NULL,
    checkout_date DATE    NOT NULL,
    roomid        INTEGER NOT NULL,
    CONSTRAINT checkout_after_checkin CHECK (checkout_date > checkin_date),
    CONSTRAINT names_not_blank CHECK (btrim(firstname) <> '' AND btrim(lastname) <> ''),
    -- same room, overlapping [checkin, checkout) ranges: the DB rejects it, API maps to 409
    CONSTRAINT no_double_booking EXCLUDE USING gist (roomid WITH =, daterange(checkin_date, checkout_date) WITH &&)
);
-- no seed rows: tests create their own data through the API

-- test-side role: SELECT only, so the DB itself rejects any write from db_client
CREATE ROLE reader LOGIN PASSWORD 'reader';
GRANT SELECT ON bookings TO reader;
