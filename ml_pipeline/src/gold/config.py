BAIRRO_RAW = "ATENDIMENTO_BAIRRO_NOME"
ANO_RAW = "OCORRENCIA_ANO"
MES_RAW = "OCORRENCIA_MES"
ANO_CENSO_2010 = 2010
ANO_CENSO_2022 = 2022

CATEGORIAS_CATALOGO = (
    ("ACIDENTE_TRANSITO", "Acidente de trânsito", 1),
    ("ATENDIMENTO_OPERACIONAL_ASSISTENCIAL", "Atendimento operacional e assistencial", 2),
    ("CRIME_PATRIMONIAL", "Crime patrimonial", 3),
    ("CRIME_VIOLENTO", "Crime violento", 4),
    ("CRIME_ORDEM_PUBLICA", "Crime contra a ordem pública", 5),
    ("CRIME_DROGAS_SUBSTANCIAS", "Drogas e substâncias", 6),
)
CATEGORIAS_MODELADAS = tuple(codigo for codigo, _, _ in CATEGORIAS_CATALOGO)

INDICADORES_CATALOGO = (
    ("RENDIMENTO_MEDIO_RESPONSAVEL_SM", "Rendimento médio do responsável", "salários mínimos", 1),
    ("PCT_ALFABETIZACAO_15_MAIS", "Alfabetização da população com 15 anos ou mais", "percentual", 2),
    ("PCT_SEM_BANHEIRO_SANITARIO", "Domicílios sem banheiro sanitário", "percentual", 3),
    ("PCT_ESGOTAMENTO_PRECARIO", "Domicílios com esgotamento precário", "percentual", 4),
    ("PCT_SEM_REDE_GERAL_AGUA", "Domicílios sem rede geral de água", "percentual", 5),
    ("PCT_LIXO_DESTINO_INADEQUADO", "Domicílios com destino inadequado do lixo", "percentual", 6),
)

SOCIO_BASE_COLUMNS = {
    "populacao": ("populacao_2010", "populacao_2022"),
    "resp_domicilios_particulares": (
        "resp_domicilios_particulares_2010",
        "resp_domicilios_particulares_2022",
    ),
    "rendimento_medio_responsavel_sm": (
        "rendimento_medio_responsavel_sm_2010",
        "rendimento_medio_responsavel_sm_2022",
    ),
    "pop_15mais": ("pop_15mais_2010", "pop_15mais_2022"),
    "alfabetizados_15mais": (
        "alfabetizados_15mais_2010",
        "alfabetizados_15mais_2022",
    ),
    "domicilios_particulares_ocupados": (
        "domicilios_particulares_permanentes_2010",
        "domicilios_particulares_permanentemente_ocupados_2022",
    ),
    "sem_banheiro_sanitario": (
        "sem_banheiro_sanitario_2010",
        "sem_banheiro_sanitario_2022",
    ),
    "esgotamento_precario": ("esgotamento_precario_2010", "esgotamento_precario_2022"),
    "sem_rede_geral_agua": (
        "sem_rede_geral_agua_2010",
        "sem_rede_geral_agua_2022",
    ),
    "lixo_destino_inadequado": (
        "lixo_destino_inadequado_2010",
        "lixo_destino_inadequado_2022",
    ),
}

SANITATION_BASES = (
    "sem_banheiro_sanitario",
    "esgotamento_precario",
    "sem_rede_geral_agua",
    "lixo_destino_inadequado",
)

COUNT_BASES = (
    "populacao",
    "resp_domicilios_particulares",
    "pop_15mais",
    "alfabetizados_15mais",
    "analfabetos_15mais",
    "domicilios_particulares_ocupados",
    *SANITATION_BASES,
)

PERCENT_BASES = (
    "alfabetizacao_15mais",
    "analfabetismo_15mais",
    *SANITATION_BASES,
)

IQV_WEIGHTS = {
    "rendimento_medio_responsavel_sm_estimado": 1 / 3,
    "pct_alfabetizacao_15mais_estimado": 1 / 3,
    "pct_sem_banheiro_sanitario_estimado": 1 / 12,
    "pct_esgotamento_precario_estimado": 1 / 12,
    "pct_sem_rede_geral_agua_estimado": 1 / 12,
    "pct_lixo_destino_inadequado_estimado": 1 / 12,
}
LOWER_IS_BETTER_IQV_COLUMNS = {
    "pct_sem_banheiro_sanitario_estimado",
    "pct_esgotamento_precario_estimado",
    "pct_sem_rede_geral_agua_estimado",
    "pct_lixo_destino_inadequado_estimado",
}

SOCIOECONOMIC_RENAME = {
    "rendimento_medio_responsavel_sm_estimado": "rendimento_medio_responsavel_sm",
    "pct_alfabetizacao_15mais_estimado": "pct_alfabetizacao_15mais",
    "pct_sem_banheiro_sanitario_estimado": "pct_sem_banheiro_sanitario",
    "pct_esgotamento_precario_estimado": "pct_esgotamento_precario",
    "pct_sem_rede_geral_agua_estimado": "pct_sem_rede_geral_agua",
    "pct_lixo_destino_inadequado_estimado": "pct_lixo_destino_inadequado",
}

SOCIOECONOMIC_GOLD_COLUMNS = (
    "bairro_id",
    "ano",
    "tipo_estimativa",
    "rendimento_medio_responsavel_sm",
    "pct_alfabetizacao_15mais",
    "pct_sem_banheiro_sanitario",
    "pct_esgotamento_precario",
    "pct_sem_rede_geral_agua",
    "pct_lixo_destino_inadequado",
    "iqv",
)

LAGS = (1, 2, 3, 6, 12)
ROLLING_WINDOWS = (3, 6, 12)
LAG_COLUMNS = tuple(f"lag_{lag}" for lag in LAGS)
ROLLING_COLUMNS = tuple(f"media_{window}" for window in ROLLING_WINDOWS)
TEMPORAL_COLUMNS = (*LAG_COLUMNS, *ROLLING_COLUMNS)

ID_COLUMNS = (
    "bairro",
    "data",
    "categoria",
    "y",
    "ano",
    "mes",
    "tempo",
)
SOCIO_OUTPUT_COLUMNS = (
    "tipo_estimativa",
    "populacao_estimado",
    "log_pop",
    "iqv",
)
LOG_TEMPORAL_COLUMNS = tuple(f"log1p_{column}" for column in TEMPORAL_COLUMNS)
CYCLICAL_MONTH_COLUMNS = ("mes_sin_1", "mes_cos_1", "mes_sin_2", "mes_cos_2")
FEATURE_COLUMNS = (
    *TEMPORAL_COLUMNS,
    "media_historica",
    *LOG_TEMPORAL_COLUMNS,
    *CYCLICAL_MONTH_COLUMNS,
)
GOLD_COLUMNS = (*ID_COLUMNS, *SOCIO_OUTPUT_COLUMNS, *FEATURE_COLUMNS)
SORT_COLUMNS = ("bairro", "categoria", "data")
