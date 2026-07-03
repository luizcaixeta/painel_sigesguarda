import csv
import re
import sys
import unicodedata
from collections.abc import Sequence
from functools import reduce
from pathlib import Path
from typing import Literal

import pandas as pd

SRC_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from cleaning.SIGESGUARDA.cleaning_neighborhood_name import (
    BAIRROS_OFICIAIS,
    MAPA_BAIRRO,
    REGIAO_METROPOLITANA,
    VALORES_INVALIDOS_BAIRRO,
)

BRONZE_DIR = PROJECT_ROOT / "data" / "bronze"
SILVER_DIR = PROJECT_ROOT / "data" / "silver"

CURITIBA_CODIGO_MUNICIPIO = "4106902"
COLUNA_BAIRRO_NOME = "ATENDIMENTO_BAIRRO_NOME"
MergeHow = Literal["left", "right", "outer", "inner", "cross", "left_anti", "right_anti"]

def detect_delimiter(file_path: Path) -> str:
    with file_path.open("r", encoding="latin1", newline="") as file:
        sample = file.read(8192)

    try:
        return csv.Sniffer().sniff(sample, delimiters=";,").delimiter
    except csv.Error:
        return ";"

def read_csv(file_path: Path, sep: str | None = None) -> pd.DataFrame:
    return pd.read_csv(
        file_path,
        sep=sep or detect_delimiter(file_path),
        encoding="latin1",
        dtype=str,
        low_memory=False,
    )

def write_silver(df: pd.DataFrame, relative_path: str) -> Path:
    output_path = (SILVER_DIR / relative_path).with_suffix(".parquet")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    return output_path

def clean_text(value):
    if pd.isna(value):
        return pd.NA

    value = str(value).strip().lower()

    if value in {"", "nan", "none", "null"}:
        return pd.NA

    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("utf-8")
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()

    return value if value else pd.NA

def normalize_numeric(series: pd.Series, remove_thousands: bool = False) -> pd.Series:
    values = series.astype("string").str.strip()
    values = values.replace(["", "X", "x", "nan", "NaN", "None", "none"], pd.NA)

    if remove_thousands:
        values = values.str.replace(".", "", regex=False)

    values = values.str.replace(",", ".", regex=False)
    return pd.to_numeric(values, errors="coerce")

def clean_numeric_columns(
    df: pd.DataFrame,
    columns: Sequence[str],
    remove_thousands: bool = False,
) -> pd.DataFrame:
    out = df.copy()

    for column in columns:
        out[column] = normalize_numeric(out[column], remove_thousands=remove_thousands)

    return out

def clean_numeric_table(
    df: pd.DataFrame,
    keys: Sequence[str],
    columns: Sequence[str],
    context: str,
    remove_thousands: bool = False,
) -> pd.DataFrame:
    require_columns(df, [*keys, *columns], context)
    return clean_numeric_columns(df, columns, remove_thousands=remove_thousands)

def safe_pct(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return numerator / denominator.mask(denominator == 0) * 100

def require_columns(df: pd.DataFrame, columns: Sequence[str], context: str) -> None:
    missing = [column for column in columns if column not in df.columns]

    if missing:
        raise KeyError(f"{context}: colunas ausentes: {missing}")

def filter_by_string_value(
    df: pd.DataFrame,
    column: str,
    value: str,
    context: str,
) -> pd.DataFrame:
    require_columns(df, [column], context)

    return df.loc[df[column].astype("string").str.strip() == value].copy()

def filter_by_string_values(
    df: pd.DataFrame,
    column: str,
    values: Sequence[str] | set[str],
    context: str,
) -> pd.DataFrame:
    require_columns(df, [column], context)
    allowed = {str(value).strip() for value in values}

    return df.loc[df[column].astype("string").str.strip().isin(allowed)].copy()

def sum_by(
    df: pd.DataFrame,
    keys: Sequence[str],
    columns: Sequence[str],
) -> pd.DataFrame:
    return df.groupby(list(keys), as_index=False)[list(columns)].sum(min_count=1)

def aggregate_numeric_table(
    df: pd.DataFrame,
    keys: Sequence[str],
    columns: Sequence[str],
    context: str,
    remove_thousands: bool = False,
) -> pd.DataFrame:
    numeric = clean_numeric_table(
        df,
        keys,
        columns,
        context,
        remove_thousands=remove_thousands,
    )

    return sum_by(numeric, keys, columns)

def merge_one_to_one(
    tables: Sequence[pd.DataFrame],
    keys: Sequence[str],
    how: MergeHow = "outer",
) -> pd.DataFrame:
    if not tables:
        raise ValueError("At least one table is required for merge.")

    return reduce(
        lambda left, right: left.merge(
            right,
            on=list(keys),
            how=how,
            validate="1:1",
        ),
        tables,
    )

def row_sum(df: pd.DataFrame, columns: Sequence[str]) -> pd.Series:
    return df[list(columns)].sum(axis=1)


def assign_percentages(
    df: pd.DataFrame,
    denominator: str | pd.Series,
    numerators: dict[str, str],
) -> pd.DataFrame:
    denominator_values = df[denominator] if isinstance(denominator, str) else denominator

    for target, numerator in numerators.items():
        df[target] = safe_pct(df[numerator], denominator_values)

    return df

def var_range(start: int, end: int, width: int = 3) -> list[str]:
    return [f"V{i:0{width}d}" for i in range(start, end + 1)]

def standardize_neighborhood(value, strict: bool = True):
    bairro = clean_text(value)

    if pd.isna(bairro):
        return pd.NA

    if bairro in VALORES_INVALIDOS_BAIRRO or bairro in REGIAO_METROPOLITANA:
        return pd.NA

    bairro = MAPA_BAIRRO.get(bairro, bairro)

    if strict and bairro not in BAIRROS_OFICIAIS:
        return pd.NA

    return bairro

def validate_neighborhoods(df: pd.DataFrame, context: str) -> None:
    neighborhoods = {str(value) for value in df[COLUNA_BAIRRO_NOME].dropna()}
    invalid = sorted(neighborhoods - BAIRROS_OFICIAIS)

    if invalid:
        raise ValueError(f"{context}: bairros fora da lista oficial: {invalid}")

def add_year_suffix(df: pd.DataFrame, suffix: str) -> pd.DataFrame:
    return df.rename(
        columns={
            column: f"{column}_{suffix}"
            for column in df.columns
            if column != COLUNA_BAIRRO_NOME and not column.endswith(f"_{suffix}")
        }
    )

def finalize_census_base(
    df: pd.DataFrame,
    name_col: str,
    code_col: str,
    suffix: str,
    adjustments: dict[str, str],
    context: str,
) -> pd.DataFrame:
    out = df.copy()
    out[name_col] = out[name_col].apply(clean_text).replace(MAPA_BAIRRO).replace(adjustments)

    out = (
        out.drop(columns=[code_col])
        .rename(columns={name_col: COLUNA_BAIRRO_NOME})
        .sort_values(COLUNA_BAIRRO_NOME)
        .reset_index(drop=True)
    )

    out = add_year_suffix(out, suffix)
    validate_neighborhoods(out, context)

    if out[COLUNA_BAIRRO_NOME].duplicated().any():
        duplicates = sorted(
            str(value)
            for value in out.loc[
                out[COLUNA_BAIRRO_NOME].duplicated(),
                COLUNA_BAIRRO_NOME,
            ]
        )
        raise ValueError(f"{context}: duplicated neighborhoods: {duplicates}")

    return out
