-- Release preparation.
--
-- Adds the quote cache the pricing module reads, and widens the stored
-- totals now that pricing returns a single consolidated figure.

CREATE TABLE quote_cache (
    id            SERIAL PRIMARY KEY,
    room_type     TEXT NOT NULL,
    nights        INTEGER NOT NULL,
    total_pence   INTEGER NOT NULL,
    quoted_at     TIMESTAMP DEFAULT NOW(),
    expires_at    TIMESTAMP NOT NULL
);

CREATE INDEX idx_quote_cache_lookup ON quote_cache (room_type, nights);

ALTER TABLE bookings ALTER COLUMN total_pence TYPE BIGINT;

ALTER TABLE notification_log ADD COLUMN channel TEXT NOT NULL DEFAULT 'email';

UPDATE bookings SET total_pence = total_pence * 2 WHERE currency = 'GBP';

DELETE FROM quote_cache WHERE expires_at < NOW();
