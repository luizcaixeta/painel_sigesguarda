-- Write your migrate up statements here
BEGIN;

CREATE SCHEMA IF NOT EXISTS monthly_forecasts;

CREATE TABLE gold.forecast_runs (
    forecast_run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gold_batch_id UUID NOT NULL REFERENCES gold.load_batches(batch_id),
    mlflow_model_name TEXT NOT NULL,
    model_alias TEXT NOT NULL,
    mlflow_run_id TEXT NOT NULL,
    forecast_month DATE NOT NULL,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE gold.monthly_forecasts (
    forecast_run_id UUID NOT NULL,
    bairro TEXT NOT NULL,

    categoria TEXT NOT NULL CHECK (
        categoria IN (
            'ACIDENTE_TRANSITO',
            'ATENDIMENTO_OPERACIONAL_ASSISTENCIAL',
            'CRIME_PATRIMONIAL',
            'CRIME_VIOLENTO',
            'CRIME_ORDEM_PUBLICA',
            'CRIME_DROGAS_SUBSTANCIAS'
        )
    ),

    predicted_count INTEGER NOT NULL CHECK (predicted_count >= 0),
    
    PRIMARY KEY (forecast_run_id, bairro, categoria)
);

---- create above / drop below ----

BEGIN; ADD

DROP TABLE IF EXISTS gold.monthly_forecasts;
DROP TABLE IF EXISTS gold.forecast_runs;

COMMIT;

-- Write your migrate down statements here. If this migration is irreversible
-- Then delete the separator line above.