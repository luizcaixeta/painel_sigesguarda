import argparse
from pathlib import Path

import pandas as pd

from common import (
    BRONZE_DIR,
    COLUNA_BAIRRO_NOME,
    clean_text,
    read_csv,
    standardize_neighborhood,
    validate_neighborhoods,
    write_silver,
)

from cleaning.SIGESGUARDA.cleaning_natureza_descricao import (
    ACIDENTE_NATURAL,
    ACIDENTE_TRANSITO,
    ATENDIMENTO_OPERACIONAL_ASSISTENCIAL,
    CORRECOES,
    CRIME_ADMNISTRACAO_PUBLICA,
    CRIME_CRIANCA_ADOLESCENTE,
    CRIME_DROGAS_SUBSTANCIAS,
    CRIME_FRAUDE_DOCUMENTAL,
    CRIME_HONRA_DISCRIMINACAO,
    CRIME_ORDEM_PUBLICA,
    CRIME_PATRIMONIAL,
    CRIME_VIOLENTO,
    EXPLOSIVOS_E_PRODUTOS_PERIGOSOS,
    INDETERMINADO,
    MATERIAIS_OBJETOS,
    PESSOAS_DESAPARECIDAS,
    RISCO_ESTRUTURAL,
)
from cleaning.SIGESGUARDA.set_columns import (
    COLUNA_DIA_SEMANA,
    COLUNA_HORA,
    COLUNA_NATUREZA_DESCRICAO,
    COLUNAS_BINARIAS,
    COLUNAS_TEXTO,
    DEFAULT_DROP_COLUMNS,
)

HISTORICAL_FILE = "2024-02-01_sigesguarda_-_Base_de_Dados.csv"
DATE_FORMATS = {
    "historical": "%Y-%m-%d %H:%M:%S.000",
    "current": "%d/%m/%Y",
}
FLOAT_BINARY_VALUES = {"1.0": 1, "0.0": 0}
POSITIVE_BINARY_VALUES = {"sim", "y", "t", "1"}
WEEKDAY_CODES = {
    "domingo": 1,
    "segunda": 2,
    "terca": 3,
    "quarta": 4,
    "quinta": 5,
    "sexta": 6,
    "sabado": 7,
}
DAY_PERIODS = {
    "MADRUGADA": (0, 5),
    "MANHA": (6, 11),
    "TARDE": (12, 17),
    "NOITE": (18, 23),
}

NATUREZA_CATEGORIAS = {
    "CRIME_VIOLENTO": CRIME_VIOLENTO,
    "ATENDIMENTO_OPERACIONAL_ASSISTENCIAL": ATENDIMENTO_OPERACIONAL_ASSISTENCIAL,
    "ACIDENTE_TRANSITO": ACIDENTE_TRANSITO,
    "ACIDENTE_NATURAL": ACIDENTE_NATURAL,
    "CRIME_PATRIMONIAL": CRIME_PATRIMONIAL,
    "CRIME_ADMINISTRACAO_PUBLICA": CRIME_ADMNISTRACAO_PUBLICA,
    "CRIME_HONRA_DISCRIMINACAO": CRIME_HONRA_DISCRIMINACAO,
    "CRIME_CRIANCA_ADOLESCENTE": CRIME_CRIANCA_ADOLESCENTE,
    "CRIME_FRAUDE_DOCUMENTAL": CRIME_FRAUDE_DOCUMENTAL,
    "CRIME_DROGAS_SUBSTANCIAS": CRIME_DROGAS_SUBSTANCIAS,
    "CRIME_ORDEM_PUBLICA": CRIME_ORDEM_PUBLICA,
    "RISCO_ESTRUTURAL": RISCO_ESTRUTURAL,
    "EXPLOSIVOS_E_PRODUTOS_PERIGOSOS": EXPLOSIVOS_E_PRODUTOS_PERIGOSOS,
    "PESSOAS_DESAPARECIDAS": PESSOAS_DESAPARECIDAS,
    "MATERIAIS_OBJETOS": MATERIAIS_OBJETOS,
}

def input_dir() -> Path:
    return BRONZE_DIR / "sigesguarda"

def resolve_bronze_csv(filename: str) -> Path:
    path = input_dir() / filename

    if path.exists():
        return path

    matches = sorted(
        candidate
        for candidate in input_dir().glob("*.csv")
        if candidate.name.lower() == filename.lower()
    )

    if len(matches) == 1:
        return matches[0]

    if matches:
        raise FileExistsError(f"Multiple SIGESGUARDA files match {filename}: {matches}")

    raise FileNotFoundError(f"SIGESGUARDA file not found: {filename}")

def split_occurrence_date(df: pd.DataFrame, date_format: str) -> pd.DataFrame:
    dates = pd.to_datetime(
        df["OCORRENCIA_DATA"].astype("string").str.strip(),
        format=date_format,
        errors="coerce",
    )

    out = df.loc[dates.notna()].copy()
    dates = dates.loc[dates.notna()]

    out["OCORRENCIA_ANO"] = dates.dt.year.astype("Int64")
    out["OCORRENCIA_MES"] = dates.dt.month.astype("Int64")
    out["OCORRENCIA_DIA"] = dates.dt.day.astype("Int64")

    return out.drop(columns=["OCORRENCIA_DATA"])

def latest_current_file() -> Path:
    historical_path = resolve_bronze_csv(HISTORICAL_FILE)
    files = sorted(path for path in input_dir().glob("*.csv") if path != historical_path)

    if not files:
        raise FileNotFoundError("Current SIGESGUARDA file not found.")

    return files[-1]

def drop_duplicate_occurrence_codes(df: pd.DataFrame) -> pd.DataFrame:
    if "OCORRENCIA_CODIGO" not in df.columns:
        return df

    out = df.copy()
    out["OCORRENCIA_CODIGO"] = out["OCORRENCIA_CODIGO"].astype("string").str.strip()
    out["OCORRENCIA_CODIGO"] = out["OCORRENCIA_CODIGO"].replace("", pd.NA)

    with_code = out.loc[out["OCORRENCIA_CODIGO"].notna()].drop_duplicates(
        subset=["OCORRENCIA_CODIGO"],
        keep="last",
    )
    without_code = out.loc[out["OCORRENCIA_CODIGO"].isna()]

    return pd.concat([with_code, without_code], ignore_index=True, sort=False)

def combine_bronze_files() -> pd.DataFrame:
    historical = read_csv(resolve_bronze_csv(HISTORICAL_FILE), sep=";")
    current = read_csv(latest_current_file())

    historical = split_occurrence_date(historical, DATE_FORMATS["historical"])
    current = split_occurrence_date(current, DATE_FORMATS["current"])

    historical = historical.drop(columns=["ATENDIMENTO_ANO"], errors="ignore")
    current = current.drop(columns=["ATENDIMENTO_ANO"], errors="ignore")

    df = pd.concat([historical, current], ignore_index=True, sort=False)
    return drop_duplicate_occurrence_codes(df)

def apply_existing_columns(
    df: pd.DataFrame,
    columns,
    mapper,
    dtype: str | None = None,
) -> pd.DataFrame:
    out = df.copy()

    for column in columns:
        if column not in out.columns:
            continue

        out[column] = out[column].apply(mapper)

        if dtype is not None:
            out[column] = out[column].astype(dtype)

    return out

def standardize_neighborhood_column(df: pd.DataFrame) -> pd.DataFrame:
    if COLUNA_BAIRRO_NOME not in df.columns:
        return df

    out = df.copy()
    out[COLUNA_BAIRRO_NOME] = out[COLUNA_BAIRRO_NOME].apply(standardize_neighborhood)
    return out.dropna(subset=[COLUNA_BAIRRO_NOME])

def map_binary(value) -> int:
    if pd.isna(value):
        return 0

    raw = str(value).strip().lower()

    if raw in FLOAT_BINARY_VALUES:
        return FLOAT_BINARY_VALUES[raw]

    value = clean_text(value)

    if pd.isna(value):
        return 0

    return 1 if value in POSITIVE_BINARY_VALUES else 0

def map_weekday(value) -> int:
    value = clean_text(value)

    if pd.isna(value):
        return 0

    return WEEKDAY_CODES.get(value, 0)

def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    if COLUNA_HORA not in df.columns:
        return df

    out = df.copy()
    parsed = pd.to_datetime(out[COLUNA_HORA], format="%H:%M:%S", errors="coerce")

    out[f"{COLUNA_HORA}_HORA"] = parsed.dt.hour.astype("Int64")
    out[f"{COLUNA_HORA}_MINUTO"] = parsed.dt.minute.astype("Int64")

    return out.drop(columns=[COLUNA_HORA])

def add_day_periodo_features(df: pd.DataFrame) -> pd.DataFrame:
    hour_col = f"{COLUNA_HORA}_HORA"

    if hour_col not in df.columns:
        return df

    out = df.copy()
    hours = pd.to_numeric(out[hour_col], errors="coerce")

    for column, (start, end) in DAY_PERIODS.items():
        out[column] = ((hours >= start) & (hours <= end)).astype("Int64")

    return out

def build_nature_reverse_map() -> dict[str, str]:
    reverse = {}
    duplicates = {}

    for category, values in NATUREZA_CATEGORIAS.items():
        for value in values:
            if value in reverse:
                duplicates.setdefault(value, set()).update({reverse[value], category})
            reverse[value] = category

    if duplicates:
        raise ValueError(f"Nature of the occurrence in more than one category: {duplicates}")

    return reverse

def first_nature_category(row: pd.Series, reverse_map: dict[str, str]):
    for value in row.dropna():
        if value in reverse_map:
            return reverse_map[value]

    return pd.NA

def clean_nature_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    natureza = df[columns].copy()

    for column in columns:
        natureza[column] = natureza[column].apply(clean_text).replace(CORRECOES)

    return natureza

def apply_nature_categories(df: pd.DataFrame) -> pd.DataFrame:
    natureza_cols = [column for column in COLUNA_NATUREZA_DESCRICAO if column in df.columns]

    if not natureza_cols:
        return df

    out = df.copy()
    natureza = clean_nature_columns(out, natureza_cols)

    has_nature = natureza.notna().any(axis=1)
    out = out.loc[has_nature].copy()
    natureza = natureza.loc[has_nature].copy()

    is_indetermined = natureza.isin(INDETERMINADO).any(axis=1)
    out = out.loc[~is_indetermined].copy()
    natureza = natureza.loc[~is_indetermined].copy()

    reverse_map = build_nature_reverse_map()
    categories = natureza.apply(first_nature_category, axis=1, reverse_map=reverse_map)

    missing = categories.isna()
    if missing.any():
        uncategorized = {
            str(value)
            for value in natureza.loc[missing].stack().dropna()
        }
        values = sorted(
            uncategorized
            - set(reverse_map)
            - set(INDETERMINADO)
        )
        raise ValueError(f"{missing.sum()} ocorrencias sem categoria. Valores: {values}")

    out.loc[:, natureza_cols] = natureza

    for category in NATUREZA_CATEGORIAS:
        out[category] = (categories == category).astype("int64")

    if not (out[list(NATUREZA_CATEGORIAS)].sum(axis=1) == 1).all():
        raise ValueError("Cada ocorrencia deve ter exatamente uma categoria de natureza.")

    return out

def build_silver() -> pd.DataFrame:
    df = combine_bronze_files()

    df = apply_existing_columns(df, COLUNAS_TEXTO, clean_text)
    df = standardize_neighborhood_column(df)
    df = apply_existing_columns(df, COLUNAS_BINARIAS, map_binary, dtype="Int64")
    df = apply_existing_columns(df, COLUNA_DIA_SEMANA, map_weekday, dtype="Int64")
    df = add_time_features(df)
    df = add_day_periodo_features(df)
    df = apply_nature_categories(df)

    drop_columns = [column for column in DEFAULT_DROP_COLUMNS if column in df.columns]
    df = df.drop(columns=drop_columns)

    validate_neighborhoods(df, "SIGESGUARDA")
    return df

def main() -> None:
    df = build_silver()
    output_path = write_silver(df, "sigesguarda/base_unificada.parquet")
    print(f"SIGESGUARDA silver generated in {output_path}")

if __name__ == "__main__":
    main()
