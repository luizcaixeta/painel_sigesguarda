-- Write your migrate up statements here
BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS gold;

CREATE TABLE gold.load_batches (
    batch_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset text NOT NULL CHECK (dataset IN ('ml_features', 'socioeconomic_features')),
    source_path text NOT NULL,
    data_through DATE NOT NULL,
    row_count integer NOT NULL CHECK (row_count >= 0),
    loaded_at timestamptz NOT NULL DEFAULT now(),
    is_current boolean NOT NULL DEFAULT true
);

CREATE UNIQUE INDEX ux_gold_current_batch_per_dataset ON gold.load_batches (dataset) WHERE is_current;

CREATE TABLE gold.dim_categorias (
    codigo TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    ordem_exibicao SMALLINT NOT NULL UNIQUE
);

CREATE TABLE gold.dim_indicadores (
    codigo TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    unidade TEXT NOT NULL,
    ordem_exibicao SMALLINT NOT NULL UNIQUE
);

CREATE TABLE gold.dim_bairros(
    bairro_id TEXT PRIMARY KEY,
    codigo_ippuc SMALLINT NOT NULL UNIQUE CHECK (codigo_ippuc BETWEEN 1 AND 75),
    nome TEXT NOT NULL UNIQUE,
    geometry_ JSONB NOT NULL,
    geometry_source TEXT NOT NULL
);

CREATE TABLE gold.ocorrencias_mensais_ml_features (
    id bigserial PRIMARY KEY,
    batch_id uuid NOT NULL REFERENCES gold.load_batches(batch_id),
    source_row_number integer NOT NULL CHECK (source_row_number > 0),

    bairro text NOT NULL,
    data date NOT NULL,
    categoria TEXT NOT NULL REFERENCES gold.dim_categorias(codigo),

    y integer NOT NULL CHECK (y >= 0),
    ano smallint NOT NULL CHECK (ano BETWEEN 2009 AND 2028),
    mes smallint NOT NULL CHECK (mes BETWEEN 1 AND 12),
    tempo integer NOT NULL CHECK (tempo > 0),
    tipo_estimativa text NOT NULL CHECK (
        tipo_estimativa IN ('observado', 'interpolado', 'extrapolado')
    ),

    populacao_estimado bigint NOT NULL CHECK (populacao_estimado >= 0),
    log_pop double precision NOT NULL CHECK (log_pop >= 0),
    iqv double precision NOT NULL CHECK (iqv BETWEEN 0 AND 100),

    lag_1 double precision NOT NULL CHECK (lag_1 >= 0),
    lag_2 double precision NOT NULL CHECK (lag_2 >= 0),
    lag_3 double precision NOT NULL CHECK (lag_3 >= 0),
    lag_6 double precision NOT NULL CHECK (lag_6 >= 0),
    lag_12 double precision NOT NULL CHECK (lag_12 >= 0),
    media_3 double precision NOT NULL CHECK (media_3 >= 0),
    media_6 double precision NOT NULL CHECK (media_6 >= 0),
    media_12 double precision NOT NULL CHECK (media_12 >= 0),
    media_historica double precision NOT NULL CHECK (media_historica >= 0),

    log1p_lag_1 double precision NOT NULL CHECK (log1p_lag_1 >= 0),
    log1p_lag_2 double precision NOT NULL CHECK (log1p_lag_2 >= 0),
    log1p_lag_3 double precision NOT NULL CHECK (log1p_lag_3 >= 0),
    log1p_lag_6 double precision NOT NULL CHECK (log1p_lag_6 >= 0),
    log1p_lag_12 double precision NOT NULL CHECK (log1p_lag_12 >= 0),
    log1p_media_3 double precision NOT NULL CHECK (log1p_media_3 >= 0),
    log1p_media_6 double precision NOT NULL CHECK (log1p_media_6 >= 0),
    log1p_media_12 double precision NOT NULL CHECK (log1p_media_12 >= 0),

    mes_sin_1 double precision NOT NULL CHECK (mes_sin_1 BETWEEN -1.000001 AND 1.000001),
    mes_cos_1 double precision NOT NULL CHECK (mes_cos_1 BETWEEN -1.000001 AND 1.000001),
    mes_sin_2 double precision NOT NULL CHECK (mes_sin_2 BETWEEN -1.000001 AND 1.000001),
    mes_cos_2 double precision NOT NULL CHECK (mes_cos_2 BETWEEN -1.000001 AND 1.000001),

    loaded_at timestamptz NOT NULL DEFAULT now(),

    UNIQUE (batch_id, source_row_number),
    UNIQUE (batch_id, bairro, categoria, data)
);

CREATE TABLE gold.indicadores_socioeconomicos_anuais (
    id bigserial PRIMARY KEY,
    batch_id uuid NOT NULL REFERENCES gold.load_batches(batch_id),
    source_row_number INTEGER NOT NULL CHECK (source_row_number > 0),

    bairro_id TEXT NOT NULL REFERENCES gold.dim_bairros(bairro_id),
    ano SMALLINT NOT NULL CHECK (ano BETWEEN 2009 AND 2050),

    tipo_estimativa TEXT NOT NULL CHECK (tipo_estimativa IN ('observado', 'interpolado', 'extrapolado')),
    rendimento_medio_responsavel_sm DOUBLE PRECISION NOT NULL CHECK (rendimento_medio_responsavel_sm >= 0),
    pct_alfabetizacao_15mais DOUBLE PRECISION NOT NULL CHECK (pct_alfabetizacao_15mais BETWEEN 0 AND 100),
    pct_sem_banheiro_sanitario DOUBLE PRECISION NOT NULL CHECK (pct_sem_banheiro_sanitario BETWEEN 0 AND 100),
    pct_esgotamento_precario DOUBLE PRECISION NOT NULL CHECK (pct_esgotamento_precario BETWEEN 0 AND 100),
    pct_sem_rede_geral_agua DOUBLE PRECISION NOT NULL CHECK (pct_sem_rede_geral_agua BETWEEN 0 AND 100),
    pct_lixo_destino_inadequado DOUBLE PRECISION NOT NULL CHECK (pct_lixo_destino_inadequado BETWEEN 0 AND 100),
    iqv DOUBLE PRECISION NOT NULL CHECK (iqv BETWEEN 0 AND 100),

    loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (batch_id, source_row_number),
    UNIQUE (batch_id, bairro_id, ano)
);

CREATE INDEX idx_gold_ml_features_batch ON gold.ocorrencias_mensais_ml_features (batch_id);
CREATE INDEX idx_gold_ml_features_bairro_data ON gold.ocorrencias_mensais_ml_features (bairro, data);
CREATE INDEX idx_gold_ml_features_categoria_data ON gold.ocorrencias_mensais_ml_features (categoria, data);

COMMIT;

---- create above / drop below ----

BEGIN;

DROP TABLE IF EXISTS gold.indicadores_socioeconomicos_anuais;
DROP TABLE IF EXISTS gold.ocorrencias_mensais_ml_features;
DROP TABLE IF EXISTS gold.dim_categorias;
DROP TABLE IF EXISTS gold.dim_indicadores;
DROP TABLE IF EXISTS gold.dim_bairros;
DROP TABLE IF EXISTS gold.load_batches;
DROP SCHEMA IF EXISTS gold;

COMMIT;

-- Write your migrate down statements here. If this migration is irreversible
-- Then delete the separator line above.
