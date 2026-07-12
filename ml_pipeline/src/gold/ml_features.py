from collections.abc import Iterable, Sequence
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SILVER_DIR = PROJECT_ROOT / "data" / "silver"
GOLD_DIR = PROJECT_ROOT / "data" / "gold"

SIGESGUARDA_SILVER_PATH = SILVER_DIR / "sigesguarda" / "base_unificada.parquet"
IBGE_2010_SILVER_PATH = SILVER_DIR / "ibge2010" / "base_bairros_2010.parquet"
IBGE_2022_SILVER_PATH = SILVER_DIR / "ibge2022" / "base_bairros_2022.parquet"
GOLD_RELATIVE_PATH = "ml_features/ocorrencias_mensais.parquet"

BAIRRO_RAW = "ATENDIMENTO_BAIRRO_NOME"
ANO_RAW = "OCORRENCIA_ANO"
MES_RAW = "OCORRENCIA_MES"
ANO_CENSO_2010 = 2010
ANO_CENSO_2022 = 2022

CATEGORIAS_MODELADAS = (
    "ACIDENTE_TRANSITO",
    "ATENDIMENTO_OPERACIONAL_ASSISTENCIAL",
    "CRIME_PATRIMONIAL",
    "CRIME_VIOLENTO",
    "CRIME_ORDEM_PUBLICA",
    "CRIME_DROGAS_SUBSTANCIAS",
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

def estimated_column(base: str) -> str:
    return f"{base}_estimado"

def pct_column(base: str) -> str:
    return f"pct_{base}_estimado"

def require_columns(df: pd.DataFrame, columns: Sequence[str], context: str) -> None:
    missing = sorted(set(columns) - set(df.columns))

    if missing:
        raise KeyError(f"{context}: colunas ausentes: {missing}")

def read_parquet(path: Path, context: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"{context}: parquet nao encontrado em {path}. "
            "Execute a pipeline silver antes de gerar a gold."
        )

    return pd.read_parquet(path)

def coerce_numeric(df: pd.DataFrame, columns: Sequence[str]) -> pd.DataFrame:
    out = df.copy()

    for column in columns:
        out[column] = pd.to_numeric(out[column], errors="coerce")

    return out

def sort_by_model_keys(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values(list(SORT_COLUMNS), kind="mergesort")

def safe_pct(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return numerator / denominator.mask(denominator == 0) * 100

def estimate_type(year: int) -> str:
    if year in {ANO_CENSO_2010, ANO_CENSO_2022}:
        return "observado"

    if ANO_CENSO_2010 < year < ANO_CENSO_2022:
        return "interpolado"

    return "extrapolado"

def normalize(values: pd.Series, *, lower_is_better: bool = False) -> pd.Series:
    values = pd.to_numeric(values, errors="coerce")
    minimum = values.min()
    maximum = values.max()
    diff = maximum - minimum

    if pd.isna(diff) or diff == 0:
        return pd.Series(0.0, index=values.index)

    if lower_is_better:
        return (maximum - values) / diff

    return (values - minimum) / diff

def required_census_columns() -> tuple[list[str], list[str]]:
    column_pairs = tuple(SOCIO_BASE_COLUMNS.values())
    return (
        [BAIRRO_RAW, *(pair[0] for pair in column_pairs)],
        [
            BAIRRO_RAW,
            "pct_alfabetizacao_15mais_2022",
            *(pair[1] for pair in column_pairs),
        ],
    )

def prepare_census_base(
    ibge_2010: pd.DataFrame,
    ibge_2022: pd.DataFrame,
) -> pd.DataFrame:
    columns_2010, columns_2022 = required_census_columns()
    require_columns(ibge_2010, columns_2010, "IBGE 2010 silver")
    require_columns(ibge_2022, columns_2022, "IBGE 2022 silver")

    census = ibge_2010[columns_2010].merge(
        ibge_2022[columns_2022],
        on=BAIRRO_RAW,
        how="inner",
        validate="1:1",
    )

    numeric_columns = [
        column for pair in SOCIO_BASE_COLUMNS.values() for column in pair
    ]
    return coerce_numeric(census, [*numeric_columns, "pct_alfabetizacao_15mais_2022"])

def build_year_frame(years: Iterable[int]) -> pd.DataFrame:
    unique_years = sorted({int(year) for year in years})
    return pd.DataFrame(
        {
            "ano": unique_years,
            "tipo_estimativa": [estimate_type(year) for year in unique_years],
        }
    )

def interpolate_socioeconomic_columns(
    census: pd.DataFrame,
    years: Iterable[int],
) -> pd.DataFrame:
    estimates = census.merge(build_year_frame(years), how="cross")
    year_ratio = (estimates["ano"] - ANO_CENSO_2010) / (
        ANO_CENSO_2022 - ANO_CENSO_2010
    )

    for target, (column_2010, column_2022) in SOCIO_BASE_COLUMNS.items():
        estimates[estimated_column(target)] = (
            estimates[column_2010]
            + (estimates[column_2022] - estimates[column_2010]) * year_ratio
        )

    return estimates.rename(columns={BAIRRO_RAW: "bairro"})

def add_literacy_estimates(estimates: pd.DataFrame) -> pd.DataFrame:
    out = estimates.copy()
    pop_15mais = out[estimated_column("pop_15mais")]

    out[pct_column("alfabetizacao_15mais")] = safe_pct(
        out[estimated_column("alfabetizados_15mais")],
        pop_15mais,
    )
    post_2022 = out["ano"] > ANO_CENSO_2022
    out.loc[post_2022, pct_column("alfabetizacao_15mais")] = out.loc[
        post_2022,
        "pct_alfabetizacao_15mais_2022",
    ]
    out[pct_column("alfabetizacao_15mais")] = out[
        pct_column("alfabetizacao_15mais")
    ].clip(lower=0, upper=100)

    out[estimated_column("alfabetizados_15mais")] = (
        pop_15mais * out[pct_column("alfabetizacao_15mais")] / 100
    )
    out[estimated_column("analfabetos_15mais")] = (
        pop_15mais - out[estimated_column("alfabetizados_15mais")]
    )
    out[pct_column("analfabetismo_15mais")] = safe_pct(
        out[estimated_column("analfabetos_15mais")],
        pop_15mais,
    )
    invalid_population = pop_15mais <= 0
    literacy_pct_columns = [
        pct_column("alfabetizacao_15mais"),
        pct_column("analfabetismo_15mais"),
    ]
    out.loc[invalid_population, literacy_pct_columns] = np.nan

    return out

def add_sanitation_percentages(estimates: pd.DataFrame) -> pd.DataFrame:
    out = estimates.copy()
    households = estimated_column("domicilios_particulares_ocupados")
    sanitation_columns = [estimated_column(base) for base in SANITATION_BASES]

    out[households] = out[households].clip(lower=0)
    out[sanitation_columns] = out[sanitation_columns].clip(lower=0)

    for column in sanitation_columns:
        out[column] = out[column].where(out[column] <= out[households], out[households])

    for base in SANITATION_BASES:
        out[pct_column(base)] = safe_pct(out[estimated_column(base)], out[households])

    invalid_households = out[households] <= 0
    sanitation_pct_columns = [pct_column(base) for base in SANITATION_BASES]
    out.loc[invalid_households, sanitation_pct_columns] = np.nan
    return out

def add_iqv(estimates: pd.DataFrame) -> pd.DataFrame:
    out = estimates.copy()
    out["iqv"] = 100 * sum(
        normalize(
            out[column],
            lower_is_better=column in LOWER_IS_BETTER_IQV_COLUMNS,
        )
        * weight
        for column, weight in IQV_WEIGHTS.items()
    )
    return out

def finalize_socioeconomic_estimates(estimates: pd.DataFrame) -> pd.DataFrame:
    out = estimates.copy()

    integer_columns = [estimated_column(base) for base in COUNT_BASES]
    rounded_columns = [
        estimated_column("rendimento_medio_responsavel_sm"),
        *[pct_column(base) for base in PERCENT_BASES],
    ]

    out[integer_columns] = out[integer_columns].round(0).astype("Int64")
    out[rounded_columns] = out[rounded_columns].round(2)
    out = add_iqv(out)
    out["log_pop"] = np.log1p(out[estimated_column("populacao")].astype("float64"))

    return out[
        ["bairro", "ano", "tipo_estimativa", "populacao_estimado", "log_pop", "iqv"]
    ].copy()

def build_socioeconomic_estimates(
    ibge_2010: pd.DataFrame,
    ibge_2022: pd.DataFrame,
    years: Iterable[int],
) -> pd.DataFrame:
    estimates = interpolate_socioeconomic_columns(
        prepare_census_base(ibge_2010, ibge_2022),
        years,
    )
    estimates = add_literacy_estimates(estimates)
    estimates = add_sanitation_percentages(estimates)
    return finalize_socioeconomic_estimates(estimates)

def prepare_occurrences(sigesguarda: pd.DataFrame) -> pd.DataFrame:
    required_columns = [BAIRRO_RAW, ANO_RAW, MES_RAW, *CATEGORIAS_MODELADAS]
    require_columns(sigesguarda, required_columns, "SIGESGUARDA silver")

    occurrences = coerce_numeric(sigesguarda[required_columns], [ANO_RAW, MES_RAW])
    occurrences = occurrences.dropna(subset=[BAIRRO_RAW, ANO_RAW, MES_RAW])

    occurrences[list(CATEGORIAS_MODELADAS)] = (
        occurrences[list(CATEGORIAS_MODELADAS)]
        .apply(pd.to_numeric, errors="coerce")
        .fillna(0)
        .astype("int64")
    )

    occurrences["data"] = pd.to_datetime(
        {
            "year": occurrences[ANO_RAW].astype("int64"),
            "month": occurrences[MES_RAW].astype("int64"),
            "day": 1,
        }
    )

    return occurrences

def monthly_counts(occurrences: pd.DataFrame) -> pd.DataFrame:
    long = occurrences.melt(
        id_vars=[BAIRRO_RAW, "data"],
        value_vars=CATEGORIAS_MODELADAS,
        var_name="categoria",
        value_name="flag_categoria",
    ).rename(columns={BAIRRO_RAW: "bairro"})

    return long.groupby(["bairro", "data", "categoria"], as_index=False).agg(
        y=("flag_categoria", "sum")
    )

def complete_monthly_panel(occurrences: pd.DataFrame) -> pd.DataFrame:
    counts = monthly_counts(occurrences)
    bairros = sorted(occurrences[BAIRRO_RAW].dropna().unique())
    dates = pd.date_range(counts["data"].min(), counts["data"].max(), freq="MS")

    panel_index = pd.MultiIndex.from_product(
        [bairros, dates, CATEGORIAS_MODELADAS],
        names=["bairro", "data", "categoria"],
    )
    panel = panel_index.to_frame(index=False).merge(
        counts,
        on=["bairro", "data", "categoria"],
        how="left",
        validate="1:1",
    )

    panel["y"] = panel["y"].fillna(0).astype("int64")
    panel["ano"] = panel["data"].dt.year.astype("int64")
    panel["mes"] = panel["data"].dt.month.astype("int64")
    panel["tempo"] = (
        (panel["data"].dt.year - panel["data"].dt.year.min()) * 12
        + panel["data"].dt.month
    ).astype("int64")

    return panel

def assert_socioeconomic_complete(panel: pd.DataFrame) -> None:
    missing = panel[list(SOCIO_OUTPUT_COLUMNS)].isna()

    if not missing.any(axis=None):
        return

    missing_rows = panel.loc[
        missing.any(axis=1),
        ["bairro", "ano"],
    ].drop_duplicates()
    raise ValueError(
        "Gold ML features: indicadores socioeconomicos ausentes para "
        f"{missing_rows.to_dict(orient='records')}"
    )

def add_temporal_features(panel: pd.DataFrame) -> pd.DataFrame:
    out = sort_by_model_keys(panel).reset_index(drop=True)
    grouped_y = out.groupby(["bairro", "categoria"])["y"]

    for lag in LAGS:
        out[f"lag_{lag}"] = grouped_y.shift(lag)

    for window in ROLLING_WINDOWS:
        out[f"media_{window}"] = grouped_y.transform(
            lambda series: series.shift(1).rolling(window=window, min_periods=1).mean()
        )

    out["media_historica"] = grouped_y.transform(
        lambda series: series.shift(1).expanding(min_periods=1).mean()
    )
    return out

def add_model_transforms(panel: pd.DataFrame) -> pd.DataFrame:
    out = panel.dropna(subset=TEMPORAL_COLUMNS).copy()

    for column in TEMPORAL_COLUMNS:
        out[f"log1p_{column}"] = np.log1p(out[column])

    for harmonic in (1, 2):
        radians = 2 * np.pi * harmonic * out["mes"] / 12
        out[f"mes_sin_{harmonic}"] = np.sin(radians)
        out[f"mes_cos_{harmonic}"] = np.cos(radians)

    return out

def finalize_gold_schema(df: pd.DataFrame) -> pd.DataFrame:
    out = df.loc[:, list(GOLD_COLUMNS)].copy()

    string_columns = ("bairro", "categoria", "tipo_estimativa")
    integer_columns = ("y", "ano", "mes", "tempo", "populacao_estimado")
    non_float_columns = {*string_columns, "data", *integer_columns}
    float_columns = [
        column for column in GOLD_COLUMNS if column not in non_float_columns
    ]

    out["data"] = pd.to_datetime(out["data"])

    out[list(string_columns)] = out[list(string_columns)].astype("string")
    out[list(integer_columns)] = (
        out[list(integer_columns)].apply(pd.to_numeric, errors="raise").astype("int64")
    )
    out[float_columns] = (
        out[float_columns].apply(pd.to_numeric, errors="raise").astype("float64")
    )

    missing_columns = out.columns[out.isna().any()].tolist()
    if missing_columns:
        raise ValueError(f"Gold ML features: colunas com nulos: {missing_columns}")

    return sort_by_model_keys(out).reset_index(drop=True)

def build_monthly_panel(
    occurrences: pd.DataFrame,
    socioeconomic: pd.DataFrame,
) -> pd.DataFrame:
    panel = complete_monthly_panel(occurrences).merge(
        socioeconomic,
        on=["bairro", "ano"],
        how="left",
        validate="many_to_one",
    )
    assert_socioeconomic_complete(panel)

    panel = add_temporal_features(panel)
    panel = add_model_transforms(panel)
    return finalize_gold_schema(panel)

def build_gold() -> pd.DataFrame:
    occurrences = prepare_occurrences(
        read_parquet(SIGESGUARDA_SILVER_PATH, "SIGESGUARDA silver")
    )
    ibge_2010 = read_parquet(IBGE_2010_SILVER_PATH, "IBGE 2010 silver")
    ibge_2022 = read_parquet(IBGE_2022_SILVER_PATH, "IBGE 2022 silver")

    years = occurrences["data"].dt.year.unique()
    socioeconomic = build_socioeconomic_estimates(ibge_2010, ibge_2022, years)
    return build_monthly_panel(occurrences, socioeconomic)

def write_gold(df: pd.DataFrame, relative_path: str = GOLD_RELATIVE_PATH) -> Path:
    output_path = (GOLD_DIR / relative_path).with_suffix(".parquet")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    return output_path
