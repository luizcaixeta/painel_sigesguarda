-- Write your migrate up statements here
BEGIN;

CREATE SCHEMA IF NOT EXISTS bronze;

CREATE TABLE bronze.raw_files (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source text NOT NULL, 
    file_name text NOT NULL,
    file_path text NOT NULL,
    file_size_bytes bigint NOT NULL,
    loaded_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (source, file_name)
);

CREATE TABLE bronze.raw_records (
    id bigserial PRIMARY KEY, 
    raw_file_id uuid NOT NULL REFERENCES
    bronze.raw_files(id),
    source text NOT NULL,
    row_number integer NOT NULL,
    payload jsonb NOT NULL,
    loaded_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (raw_file_id, row_number)
);

COMMIT;

---- create above / drop below ----

BEGIN;

DROP TABLE IF EXISTS bronze.raw_records;
DROP TABLE IF EXISTS bronze.raw_files;
DROP SCHEMA IF EXISTS bronze;

COMMIT;

-- Write your migrate down statements here. If this migration is irreversible
-- Then delete the separator line above.
