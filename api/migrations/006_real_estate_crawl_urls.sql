-- Write your migrate up statements here

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS bronze.real_estate_crawl_urls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_slug TEXT NOT NULL,
    canonical_url TEXT NOT NULL,
    url_hash TEXT NOT NULL,
    external_id TEXT,
    status TEXT NOT NULL CHECK (
        status IN (
            'discovered',
            'processed',
            'rejected',
            'retry'
        )
    ),
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_fetched_at TIMESTAMPTZ,
    lastmod TEXT,
    http_status INTEGER,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    content_hash TEXT,
    rejection_reason TEXT,
    UNIQUE (source_slug, url_hash)
);

CREATE INDEX idx_real_estate_crawl_urls_source_status
    ON bronze.real_estate_crawl_urls (source_slug, status);

COMMIT;

---- create above / drop below ----

BEGIN;

DROP TABLE IF EXISTS bronze.real_estate_crawl_urls;

COMMIT;

-- Write your migrate down statements here. If this migration is irreversible
-- Then delete the separator line above.
