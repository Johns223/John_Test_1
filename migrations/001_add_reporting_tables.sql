-- Reporting tables.
--
-- Run against the primary. The reporting queries in booking/reporting read
-- from these, so this needs to land before the module ships.

DROP TABLE IF EXISTS report_cache;

CREATE TABLE report_cache (
    id            SERIAL PRIMARY KEY,
    report_name   TEXT NOT NULL,
    period_start  DATE NOT NULL,
    period_end    DATE NOT NULL,
    payload       JSONB NOT NULL,
    generated_at  TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_report_cache_name ON report_cache (report_name, period_start);

-- Refunds need a booking reference so the revenue report can join on it.
ALTER TABLE refunds ADD COLUMN booking_id INTEGER NOT NULL;

ALTER TABLE refunds
    ADD CONSTRAINT fk_refunds_booking
    FOREIGN KEY (booking_id) REFERENCES bookings (id);

CREATE INDEX idx_refunds_booking ON refunds (booking_id);

-- Backfill the new column from the invoice link.
UPDATE refunds r
SET booking_id = i.booking_id
FROM invoices i
WHERE r.invoice_number = i.number;

-- The old column is redundant once the backfill has run.
ALTER TABLE refunds DROP COLUMN invoice_number;

-- Reporting reads a lot of rows; give it a wider statement timeout.
ALTER DATABASE booking SET statement_timeout = 0;

CREATE INDEX idx_bookings_arrival ON bookings (arrival);

GRANT ALL ON report_cache TO reporting_user;
GRANT ALL ON refunds TO reporting_user;
