import argparse
import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
import psycopg
from psycopg import sql

from gold.config import CATEGORIAS_CATALOGO, INDICADORES_CATALOGO
from gold.load_dim_bairros import load_dim_bairros, load_features
from gold.ml_features import (
    GOLD_COLUMNS,
    GOLD_DIR,
    GOLD_RELATIVE_PATH,
    SOCIOECONOMIC_GOLD_COLUMNS,
    SOCIOECONOMIC_GOLD_RELATIVE_PATH,
)


@dataclass(frozen=True)
class GoldDataset:
    name: str
    relative_path: str
    table: str
    columns: tuple[str, ...]

    @property
    def path(self) -> Path:
        return GOLD_DIR / self.relative_path

    @property
    def table_identifier(self) -> sql.Identifier:
        return sql.Identifier(*self.table.split("."))


DATASETS = {
    "ml_features": GoldDataset(
        name="ml_features",
        relative_path=GOLD_RELATIVE_PATH,
        table="gold.ocorrencias_mensais_ml_features",
        columns=GOLD_COLUMNS,
    ),
    "socioeconomic_features": GoldDataset(
        name="socioeconomic_features",
        relative_path=SOCIOECONOMIC_GOLD_RELATIVE_PATH,
        table="gold.indicadores_socioeconomicos_anuais",
        columns=SOCIOECONOMIC_GOLD_COLUMNS,
    ),
}

CATEGORIAS_UPSERT = """
    INSERT INTO gold.dim_categorias (codigo, nome, ordem_exibicao)
    VALUES (%s, %s, %s)
    ON CONFLICT (codigo) DO UPDATE
    SET nome = EXCLUDED.nome,
        ordem_exibicao = EXCLUDED.ordem_exibicao
"""

INDICADORES_UPSERT = """
    INSERT INTO gold.dim_indicadores (codigo, nome, unidade, ordem_exibicao)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (codigo) DO UPDATE
    SET nome = EXCLUDED.nome,
        unidade = EXCLUDED.unidade,
        ordem_exibicao = EXCLUDED.ordem_exibicao
"""


def load_catalogs(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        cur.executemany(CATEGORIAS_UPSERT, CATEGORIAS_CATALOGO)
        cur.executemany(INDICADORES_UPSERT, INDICADORES_CATALOGO)

    print(
        f"Loaded {len(CATEGORIAS_CATALOGO)} categories and "
        f"{len(INDICADORES_CATALOGO)} indicators into Gold catalogs"
    )

def read_gold_parquet(dataset: GoldDataset) -> pd.DataFrame:
    if not dataset.path.exists():
        raise FileNotFoundError(
            f"Gold Parquet not found for {dataset.name}: {dataset.path}. "
            "Run the gold pipeline before loading PostgreSQL."
        )

    df = pd.read_parquet(dataset.path)
    validate_columns(df, dataset)
    return df.loc[:, list(dataset.columns)]

def validate_columns(df: pd.DataFrame, dataset: GoldDataset) -> None:
    actual = set(df.columns)
    expected = set(dataset.columns)
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)

    if missing or unexpected:
        messages = []

        if missing:
            messages.append(f"missing columns: {missing}")

        if unexpected:
            messages.append(f"unexpected columns: {unexpected}")

        raise ValueError(f"{dataset.name}: invalid gold schema; " + "; ".join(messages))

def to_db_value(value: Any) -> Any:
    if pd.isna(value):
        return None

    if isinstance(value, pd.Timestamp):
        return value.date()

    if hasattr(value, "item"):
        return value.item()

    return value

def create_load_batch(
    cur: psycopg.Cursor,
    dataset: GoldDataset,
    df: pd.DataFrame,
    data_through: date,
) -> str:
    cur.execute(
        """
        UPDATE gold.load_batches
        SET is_current = false
        WHERE dataset = %s
        """,
        (dataset.name,),
    )

    cur.execute(
        """
        INSERT INTO gold.load_batches (
            dataset,
            source_path,
            data_through,
            row_count,
            is_current
        )
        VALUES (%s, %s, %s, %s, true)
        RETURNING batch_id
        """,
        (
            dataset.name,
            str(dataset.path),
            data_through,
            len(df),
        ),
    )

    row = cur.fetchone()

    if row is None:
        raise RuntimeError(f"{dataset.name}: failed to create gold load batch.")

    return str(row[0])

def copy_dataframe_to_table(
    cur: psycopg.Cursor,
    dataset: GoldDataset,
    batch_id: str,
    df: pd.DataFrame,
) -> None:
    insert_columns = ("batch_id", "source_row_number", *dataset.columns)
    copy_sql = sql.SQL("COPY {} ({}) FROM STDIN").format(
        dataset.table_identifier,
        sql.SQL(", ").join(sql.Identifier(column) for column in insert_columns),
    )

    with cur.copy(copy_sql) as copy:
        for source_row_number, row in enumerate(
            df.itertuples(index=False, name=None),
            start=1,
        ):
            copy.write_row(
                (
                    batch_id,
                    source_row_number,
                    *(to_db_value(value) for value in row),
                )
            )

def resolve_data_through(dataset: GoldDataset, df: pd.DataFrame) -> date:

    if dataset.name == "ml_features":
        return pd.to_datetime(df["data"]).max().date()

    if dataset.name == "socioeconomic_features":
        latest_year = int(df["ano"].max())
        return date(latest_year, 12, 31)

    raise ValueError(f'{dataset.name}: unsupported dataset')

def load_dataset(conn: psycopg.Connection, dataset: GoldDataset) -> None:
    df = read_gold_parquet(dataset)

    with conn.cursor() as cur:
        data_through = resolve_data_through(dataset, df)
        batch_id = create_load_batch(cur, dataset, df, data_through)

        if not df.empty:
            copy_dataframe_to_table(cur, dataset, batch_id, df)

    print(f"Loaded {len(df)} rows from {dataset.path} into {dataset.table}")

def resolve_datasets(source: str) -> list[GoldDataset]:
    if source == "all":
        return list(DATASETS.values())

    if source == "dim_bairros":
        return []

    return [DATASETS[source]]

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load gold Parquet datasets into PostgreSQL."
    )
    parser.add_argument(
        "--source",
        choices=["all", "ml_features", "dim_bairros"],
        default="all",
        help="Load all gold datasets or only one source.",
    )
    parser.add_argument(
        "--dsn",
        default=os.getenv("SIGESGUARDA_DB_DSN"),
        help="PostgreSQL DSN. Defaults to SIGESGUARDA_DB_DSN.",
    )

    return parser.parse_args()

def main() -> None:
    args = parse_args()

    if not args.dsn:
        raise RuntimeError(
            "Database DSN not provided. Set SIGESGUARDA_DB_DSN or use --dsn."
        )

    datasets = resolve_datasets(args.source)

    with psycopg.connect(args.dsn) as conn:
        load_catalogs(conn)

        if args.source in {"all", "dim_bairros"}:
            load_dim_bairros(conn, load_features())
        for dataset in datasets:
            load_dataset(conn, dataset)

        conn.commit()

if __name__ == "__main__":
    main()
