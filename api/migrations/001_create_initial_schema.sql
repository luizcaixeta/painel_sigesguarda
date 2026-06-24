-- Write your migrate up statements here
BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE bairros (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    nome text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE categorias_ocorrencia (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    codigo text NOT NULL UNIQUE,
    descricao text NOT NULL,
    ativa boolean NOT NULL DEFAULT true 
);

CREATE TABLE sigesguarda_ocorrencias (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    bairro_id uuid NOT NULL REFERENCES bairros(id),
    categoria_id uuid NOT NULL REFERENCES categorias_ocorrencia(id),
    dia_ocorrencia smallint NOT NULL,
    ano smallint NOT NULL, 
    ocorrencia_mes smallint NOT NULL CHECK (ocorrencia_mes BETWEEN 1 and 12),
    ocorrencia_dia_semana smallint NOT NULL CHECK (ocorrencia_dia_semana BETWEEN 1 AND 12),
    flag_equipamento_urbano boolean NOT NULL DEFAULT FALSE,
    madrugada boolean NOT NULL DEFAULT FALSE, 
    manha boolean NOT NULL DEFAULT FALSE, 
    tarde boolean NOT NULL DEFAULT FALSE,
    noite boolean NOT NULL DEFAULT FALSE, 
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE ibge_bairro_censo (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    bairro_id uuid NOT NULL REFERENCES bairros(id),
    ano_censo smallint NOT NULL CHECK (ano_censo IN (2009, 2026)),
    log_rendimento double precision NOT NULL, 
    log_pop double precision NOT NULL, 
    pct_alfabetizacao_15_mais double precision NOT NULL, 
    pct_sem_banheiro_sanitario double precision NOT NULL, 
    pct_esgotamento_precario double precision NOT NULL, 
    pct_sem_rede_geral_agua double precision NOT NULL, 
    pct_lixo_destino_inadequado double precision NOT NULL, 
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (bairro_id, ano_censo)
);

CREATE TABLE bairro_indicadores_anuais (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    bairro_id uuid NOT NULL REFERENCES bairros(id),
    ano_censo smallint NOT NULL CHECK (ano_censo IN (2009, 2026)),
    log_rendimento double precision NOT NULL, 
    log_pop double precision NOT NULL, 
    pct_alfabetizacao_15_mais double precision NOT NULL, 
    pct_sem_banheiro_sanitario double precision NOT NULL, 
    pct_esgotamento_precario double precision NOT NULL, 
    pct_sem_rede_geral_agua double precision NOT NULL, 
    pct_lixo_destino_inadequado double precision NOT NULL,
    metodo_estimativa text NOT NULL, 
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (bairro_id, ano_censo)
);

CREATE TABLE bairro_iqv_anual (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    bairro_id uuid NOT NULL REFERENCES bairros(id),
    ano smallint NOT NULL, 
    iqv double precision NOT NULL CHECK (iqv >= 0 AND iqv <= 100),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (bairro_id, ano)
);

CREATE TABLE model_features_contagem_mensal (
    bairro_id uuid NOT NULL REFERENCES bairros(id),
    categoria_id uuid NOT NULL REFERENCES categorias_ocorrencia(id),
    periodo_mes date NOT NULL, 
    ano smallint NOT NULL, 
    mes smallint NOT NULL CHECK (mes BETWEEN 1 AND 12),
    tempo integer NOT NULL, 
    y integer NOT NULL CHECK (y >= 0),

    lag_1 double precision NOT NULL CHECK (lag_1 >= 0),
    lag_2 double precision NOT NULL CHECK (lag_2 >= 0),
    lag_3 double precision NOT NULL CHECK (lag_3 >= 0),
    lag_6 double precision NOT NULL CHECK (lag_6 >= 0),
    lag_12 double precision NOT NULL CHECK (lag_12 >= 0),
    media_3 double precision NOT NULL CHECK (media_3 >= 0),
    media_6 double precision NOT NULL CHECK (media_6 >= 0),
    media_12 double precision NOT NULL CHECK (media_12 >= 0),

    log1p_lag_1 double precision NOT NULL,
    log1p_lag_2 double precision NOT NULL,
    log1p_lag_3 double precision NOT NULL,
    log1p_lag_6 double precision NOT NULL,
    log1p_lag_12 double precision NOT NULL,
    log1p_media_3 double precision NOT NULL,
    log1p_media_6 double precision NOT NULL,
    log1p_media_12 double precision NOT NULL,

    iqv double precision NOT NULL CHECK (iqv >= 0 AND iqv <= 100),
    log_pop double precision NOT NULL,
    mes_sin_1 double precision NOT NULL,
    mes_cos_1 double precision NOT NULL,
    mes_sin_2 double precision NOT NULL,
    mes_cos_2 double precision NOT NULL,

    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (bairro_id, categoria_id, periodo_mes)
);

CREATE INDEX idx_model_features_periodo ON model_features_contagem_mensal (periodo_mes);

COMMIT;

---- create above / drop below ----

BEGIN;

DROP TABLE IF EXISTS model_features_contagem_mensal;
DROP TABLE IF EXISTS bairro_iqv_anual;
DROP TABLE IF EXISTS bairro_indicadores_anuais;
DROP TABLE IF EXISTS ibge_bairro_censo;
DROP TABLE IF EXISTS sigesguarda_ocorrencias;
DROP TABLE IF EXISTS categorias_ocorrencia;
DROP TABLE IF EXISTS bairros;

COMMIT;

-- Write your migrate down statements here. If this migration is irreversible
-- Then delete the separator line above.
