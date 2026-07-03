-- Write your migrate up statements here
BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS silver;

CREATE TABLE silver.load_batches (
    batch_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset text NOT NULL CHECK (dataset IN ('sigesguarda', 'ibge2010', 'ibge2022')),
    source_path text NOT NULL,
    row_count integer NOT NULL CHECK (row_count >= 0),
    loaded_at timestamptz NOT NULL DEFAULT now(),
    is_current boolean NOT NULL DEFAULT true
);

CREATE UNIQUE INDEX ux_silver_current_batch_per_dataset ON silver.load_batches (dataset) WHERE is_current;

CREATE TABLE silver.sigesguarda_ocorrencias (
    id bigserial PRIMARY KEY,
    batch_id uuid NOT NULL REFERENCES silver.load_batches(batch_id),
    source_row_number integer NOT NULL CHECK (source_row_number > 0),
    atendimento_bairro_nome text NOT NULL,
    flag_equipamento_urbano smallint NOT NULL CHECK (flag_equipamento_urbano IN (0, 1)),
    flag_flagrante smallint NOT NULL CHECK (flag_flagrante IN (0,1)),
    logradouro_nome text,
    
    natureza1_defesa_civil smallint NOT NULL CHECK (natureza1_defesa_civil IN (0, 1)),
    natureza1_descricao text NOT NULL,
    natureza2_defesa_civil smallint NOT NULL CHECK (natureza2_defesa_civil IN (0, 1)),
    natureza2_descricao text,
    natureza3_defesa_civil smallint NOT NULL CHECK (natureza3_defesa_civil IN (0, 1)),
    natureza3_descricao text,
    natureza4_defesa_civil smallint NOT NULL CHECK (natureza4_defesa_civil IN (0, 1)),
    natureza4_descricao text,
    natureza5_defesa_civil smallint NOT NULL CHECK (natureza5_defesa_civil IN (0, 1)),
    natureza5_descricao text,
      
    ocorrencia_ano smallint NOT NULL CHECK (ocorrencia_ano BETWEEN 2008 AND 2028),
    ocorrencia_mes smallint NOT NULL CHECK (ocorrencia_mes BETWEEN 1 AND 12),
    ocorrencia_dia smallint NOT NULL CHECK (ocorrencia_dia BETWEEN 1 AND 31),
    ocorrencia_dia_semana smallint NOT NULL CHECK (ocorrencia_dia_semana BETWEEN 0 AND 7),
    ocorrencia_hora_hora smallint NOT NULL CHECK (ocorrencia_hora_hora BETWEEN 0 AND 23),
    ocorrencia_hora_minuto smallint NOT NULL CHECK (ocorrencia_hora_minuto BETWEEN 0 AND 59),

    secretaria_sigla text,
    servico_nome text,
    numero_protocolo_156 text,

    madrugada smallint NOT NULL CHECK (madrugada IN (0, 1)),
    manha smallint NOT NULL CHECK (manha IN (0, 1)),
    tarde smallint NOT NULL CHECK (tarde IN (0, 1)),
    noite smallint NOT NULL CHECK (noite IN (0, 1)),

    crime_violento smallint NOT NULL CHECK (crime_violento IN (0,1)),
    atendimento_operacional_assistencial smallint NOT NULL CHECK (atendimento_operacional_assistencial IN (0, 1)),
    acidente_transito smallint NOT NULL CHECK (acidente_transito IN (0, 1)),
    acidente_natural smallint NOT NULL CHECK (acidente_natural IN (0, 1)),
    crime_patrimonial smallint NOT NULL CHECK (crime_patrimonial IN (0, 1)),
    crime_administracao_publica smallint NOT NULL CHECK (crime_administracao_publica IN (0, 1)),
    crime_honra_discriminacao smallint NOT NULL CHECK (crime_honra_discriminacao IN (0, 1)),
    crime_crianca_adolescente smallint NOT NULL CHECK (crime_crianca_adolescente IN (0, 1)),
    crime_fraude_documental smallint NOT NULL CHECK (crime_fraude_documental IN (0, 1)),
    crime_drogas_substancias smallint NOT NULL CHECK (crime_drogas_substancias IN (0, 1)),
    crime_ordem_publica smallint NOT NULL CHECK (crime_ordem_publica IN (0, 1)),
    risco_estrutural smallint NOT NULL CHECK (risco_estrutural IN (0, 1)),
    explosivos_e_produtos_perigosos smallint NOT NULL CHECK (explosivos_e_produtos_perigosos IN (0, 1)),
    pessoas_desaparecidas smallint NOT NULL CHECK (pessoas_desaparecidas IN (0, 1)),
    materiais_objetos smallint NOT NULL CHECK (materiais_objetos IN (0, 1)),

    loaded_at timestamptz NOT NULL DEFAULT now(),

    UNIQUE (batch_id, source_row_number),

    CHECK (madrugada + manha + tarde + noite = 1),
    CHECK (
        crime_violento +
        atendimento_operacional_assistencial +
        acidente_transito +
        acidente_natural +
        crime_patrimonial +
        crime_administracao_publica +
        crime_honra_discriminacao +
        crime_crianca_adolescente +
        crime_fraude_documental +
        crime_drogas_substancias +
        crime_ordem_publica +
        risco_estrutural +
        explosivos_e_produtos_perigosos +
        pessoas_desaparecidas +
        materiais_objetos = 1
    )
);

CREATE INDEX idx_silver_sigesguarda_batch ON silver.sigesguarda_ocorrencias (batch_id);

CREATE INDEX idx_silver_sigesguarda_bairro_ano_mes ON silver.sigesguarda_ocorrencias (atendimento_bairro_nome, ocorrencia_ano, ocorrencia_mes);

CREATE INDEX idx_silver_sigesguarda_categoria_periodo ON silver.sigesguarda_ocorrencias (
        ocorrencia_ano,
        ocorrencia_mes,
        crime_violento,
        atendimento_operacional_assistencial,
        acidente_transito,
        acidente_natural,
        crime_patrimonial
);

CREATE TABLE silver.ibge_bairros_2010 (
    id bigserial PRIMARY KEY,
    batch_id uuid NOT NULL REFERENCES silver.load_batches(batch_id),
    source_row_number integer NOT NULL CHECK (source_row_number > 0),

    atendimento_bairro_nome text NOT NULL,

    populacao_2010 bigint NOT NULL CHECK (populacao_2010 >= 0),
    pessoas_10_anos_ou_mais_2010 bigint NOT NULL CHECK (pessoas_10_anos_ou_mais_2010 >= 0),
    pct_sem_rendimento_2010 double precision NOT NULL CHECK (pct_sem_rendimento_2010 BETWEEN 0 AND 100),
    pct_rendimento_ate_1_sm_2010 double precision NOT NULL CHECK (pct_rendimento_ate_1_sm_2010 BETWEEN 0 AND 100), 
    pct_rendimento_ate_2_sm_2010 double precision NOT NULL CHECK (pct_rendimento_ate_2_sm_2010 BETWEEN 0 AND 100),
    pct_rendimento_acima_5_sm_2010 double precision NOT NULL CHECK (pct_rendimento_acima_5_sm_2010 BETWEEN 0 AND 100),

    resp_domicilios_particulares_2010 bigint NOT NULL CHECK (resp_domicilios_particulares_2010 >= 0),
    rendimento_medio_responsavel_2010 double precision NOT NULL CHECK (rendimento_medio_responsavel_2010 >= 0),
    rendimento_medio_responsavel_sm_2010 double precision NOT NULL CHECK (rendimento_medio_responsavel_sm_2010 >= 0),

    pop_10mais_2010 bigint NOT NULL CHECK (pop_10mais_2010 >= 0),
    alfabetizados_10mais_2010 bigint NOT NULL CHECK (alfabetizados_10mais_2010 >= 0),
    pct_alfabetizacao_10mais_2010 double precision NOT NULL CHECK (pct_alfabetizacao_10mais_2010 BETWEEN 0 AND 100),
    pct_analfabetismo_10mais_2010 double precision NOT NULL CHECK (pct_analfabetismo_10mais_2010 BETWEEN 0 AND 100),

    pop_15mais_2010 bigint NOT NULL CHECK (pop_15mais_2010 >= 0),
    alfabetizados_15mais_2010 bigint NOT NULL CHECK (alfabetizados_15mais_2010 >= 0),
    analfabetos_15mais_2010 bigint NOT NULL CHECK (analfabetos_15mais_2010 >= 0),
    pct_alfabetizacao_15mais_2010 double precision NOT NULL CHECK (pct_alfabetizacao_15mais_2010 BETWEEN 0 AND 100),
    pct_analfabetismo_15mais_2010 double precision NOT NULL CHECK (pct_analfabetismo_15mais_2010 BETWEEN 0 AND 100),

    domicilios_particulares_permanentes_2010 bigint NOT NULL CHECK (domicilios_particulares_permanentes_2010 >= 0),
    sem_rede_geral_agua_2010 bigint NOT NULL CHECK (sem_rede_geral_agua_2010 >= 0),
    pct_sem_rede_geral_agua_2010 double precision NOT NULL CHECK (pct_sem_rede_geral_agua_2010 BETWEEN 0 AND 100),
    sem_banheiro_sanitario_2010 bigint NOT NULL CHECK (sem_banheiro_sanitario_2010 >= 0),
    pct_sem_banheiro_sanitario_2010 double precision NOT NULL CHECK (pct_sem_banheiro_sanitario_2010 BETWEEN 0 AND 100),
    esgotamento_precario_2010 bigint NOT NULL CHECK (esgotamento_precario_2010 >= 0),
    pct_esgotamento_precario_2010 double precision NOT NULL CHECK (pct_esgotamento_precario_2010 BETWEEN 0 AND 100),
    lixo_destino_inadequado_2010 bigint NOT NULL CHECK (lixo_destino_inadequado_2010 >= 0),
    pct_lixo_destino_inadequado_2010 double precision NOT NULL CHECK (pct_lixo_destino_inadequado_2010 BETWEEN 0 AND 100),

    loaded_at timestamptz NOT NULL DEFAULT now(),

    UNIQUE (batch_id, source_row_number),
    UNIQUE (batch_id, atendimento_bairro_nome)
);

CREATE INDEX idx_silver_ibge_bairros_2010_bairro ON silver.ibge_bairros_2010 (atendimento_bairro_nome);

CREATE TABLE silver.ibge_bairros_2022 (
    id bigserial PRIMARY KEY,
    batch_id uuid NOT NULL REFERENCES silver.load_batches(batch_id),
    source_row_number integer NOT NULL CHECK (source_row_number > 0),

    atendimento_bairro_nome text NOT NULL,

    populacao_2022 bigint NOT NULL CHECK (populacao_2022 >= 0),
    resp_domicilios_particulares_2022 bigint NOT NULL CHECK (resp_domicilios_particulares_2022 >= 0),
    moradores_domicilios_particulares_2022 bigint NOT NULL CHECK (moradores_domicilios_particulares_2022 >= 0),
    rendimento_medio_responsavel_2022 double precision NOT NULL CHECK (rendimento_medio_responsavel_2022 >= 0),
    rendimento_medio_responsavel_sm_2022 double precision NOT NULL CHECK (rendimento_medio_responsavel_sm_2022 >= 0),

    pop_15mais_2022 bigint NOT NULL CHECK (pop_15mais_2022 >= 0),
    alfabetizados_15mais_2022 bigint NOT NULL CHECK (alfabetizados_15mais_2022 >= 0),
    pct_alfabetizacao_15mais_2022 double precision NOT NULL CHECK (pct_alfabetizacao_15mais_2022 BETWEEN 0 AND 100),
    pct_analfabetismo_15mais_2022 double precision NOT NULL CHECK (pct_analfabetismo_15mais_2022 BETWEEN 0 AND 100),

    domicilios_particulares_permanentemente_ocupados_2022 bigint NOT NULL CHECK (domicilios_particulares_permanentemente_ocupados_2022 >= 0),
    sem_banheiro_sanitario_2022 bigint NOT NULL CHECK (sem_banheiro_sanitario_2022 >= 0),
    pct_sem_banheiro_sanitario_2022 double precision NOT NULL CHECK (pct_sem_banheiro_sanitario_2022 BETWEEN 0 AND 100),
    esgotamento_precario_2022 bigint NOT NULL CHECK (esgotamento_precario_2022 >= 0),
    pct_esgotamento_precario_2022 double precision NOT NULL CHECK (pct_esgotamento_precario_2022 BETWEEN 0 AND 100),
    sem_rede_geral_agua_2022 bigint NOT NULL CHECK (sem_rede_geral_agua_2022 >= 0),
    pct_sem_rede_geral_agua_2022 double precision NOT NULL CHECK (pct_sem_rede_geral_agua_2022 BETWEEN 0 AND 100),
    lixo_destino_inadequado_2022 bigint NOT NULL CHECK (lixo_destino_inadequado_2022 >= 0),
    pct_lixo_destino_inadequado_2022 double precision NOT NULL CHECK (pct_lixo_destino_inadequado_2022 BETWEEN 0 AND 100),
    domicilios_improvisados_estrutura_degradada_2022 bigint NOT NULL CHECK (domicilios_improvisados_estrutura_degradada_2022 >= 0),
    pct_domicilios_improvisados_estrutura_degradada_2022 double precision NOT NULL CHECK (pct_domicilios_improvisados_estrutura_degradada_2022 BETWEEN 0 AND 100),

    loaded_at timestamptz NOT NULL DEFAULT now(),

    UNIQUE (batch_id, source_row_number),
    UNIQUE (batch_id, atendimento_bairro_nome)
);

CREATE INDEX idx_silver_ibge_bairros_2022_bairro ON silver.ibge_bairros_2022 (atendimento_bairro_nome);

COMMIT;

---- create above / drop below ----

BEGIN;

DROP TABLE IF EXISTS silver.ibge_bairros_2022;
DROP TABLE IF EXISTS silver.ibge_bairros_2010;
DROP TABLE IF EXISTS silver.sigesguarda_ocorrencias;
DROP TABLE IF EXISTS silver.load_batches;

DROP SCHEMA IF EXISTS silver;

COMMIT;

-- Write your migrate down statements here. If this migration is irreversible
-- Then delete the separator line above.
