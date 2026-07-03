import argparse
import os
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import pandas as pd
import psycopg
from psycopg import sql

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SILVER_DIR = PROJECT_ROOT / "data" / "silver"

@dataclass(frozen=True)
class SilverDataset:
    name: str
    relative_path: str
    table: str
    columns: tuple[str, ...]

    @property
    def path(self) -> Path:
        return SILVER_DIR / self.relative_path

    @property
    def table_identifier(self) -> sql.Identifier:
        return sql.Identifier(*self.table.split("."))

SIGESGUARDA_COLUMNS = (
    "atendimento_bairro_nome",
    "flag_equipamento_urbano",
    "flag_flagrante",
    "logradouro_nome",
    "natureza1_defesa_civil",
    "natureza1_descricao",
    "natureza2_defesa_civil",
    "natureza2_descricao",
    "natureza3_defesa_civil",
    "natureza3_descricao",
    "natureza4_defesa_civil",
    "natureza4_descricao",
    "natureza5_defesa_civil",
    "natureza5_descricao",
    "ocorrencia_ano",
    "ocorrencia_dia_semana",
    "ocorrencia_mes",
    "secretaria_sigla",
    "servico_nome",
    "numero_protocolo_156",
    "ocorrencia_dia",
    "ocorrencia_hora_hora",
    "ocorrencia_hora_minuto",
    "madrugada",
    "manha",
    "tarde",
    "noite",
    "crime_violento",
    "atendimento_operacional_assistencial",
    "acidente_transito",
    "acidente_natural",
    "crime_patrimonial",
    "crime_administracao_publica",
    "crime_honra_discriminacao",
    "crime_crianca_adolescente",
    "crime_fraude_documental",
    "crime_drogas_substancias",
    "crime_ordem_publica",
    "risco_estrutural",
    "explosivos_e_produtos_perigosos",
    "pessoas_desaparecidas",
    "materiais_objetos",
)

IBGE_2010_COLUMNS = (
    "atendimento_bairro_nome",
    "populacao_2010",
    "pessoas_10_anos_ou_mais_2010",
    "pct_sem_rendimento_2010",
    "pct_rendimento_ate_1_sm_2010",
    "pct_rendimento_ate_2_sm_2010",
    "pct_rendimento_acima_5_sm_2010",
    "resp_domicilios_particulares_2010",
    "rendimento_medio_responsavel_2010",
    "rendimento_medio_responsavel_sm_2010",
    "pop_10mais_2010",
    "alfabetizados_10mais_2010",
    "pct_alfabetizacao_10mais_2010",
    "pct_analfabetismo_10mais_2010",
    "pop_15mais_2010",
    "alfabetizados_15mais_2010",
    "analfabetos_15mais_2010",
    "pct_alfabetizacao_15mais_2010",
    "pct_analfabetismo_15mais_2010",
    "domicilios_particulares_permanentes_2010",
    "sem_rede_geral_agua_2010",
    "pct_sem_rede_geral_agua_2010",
    "sem_banheiro_sanitario_2010",
    "pct_sem_banheiro_sanitario_2010",
    "esgotamento_precario_2010",
    "pct_esgotamento_precario_2010",
    "lixo_destino_inadequado_2010",
    "pct_lixo_destino_inadequado_2010",
)

IBGE_2022_COLUMNS = (
    "atendimento_bairro_nome",
    "populacao_2022",
    "resp_domicilios_particulares_2022",
    "moradores_domicilios_particulares_2022",
    "rendimento_medio_responsavel_2022",
    "rendimento_medio_responsavel_sm_2022",
    "pop_15mais_2022",
    "alfabetizados_15mais_2022",
    "pct_alfabetizacao_15mais_2022",
    "pct_analfabetismo_15mais_2022",
    "domicilios_particulares_permanentemente_ocupados_2022",
    "sem_banheiro_sanitario_2022",
    "pct_sem_banheiro_sanitario_2022",
    "esgotamento_precario_2022",
    "pct_esgotamento_precario_2022",
    "sem_rede_geral_agua_2022",
    "pct_sem_rede_geral_agua_2022",
    "lixo_destino_inadequado_2022",
    "pct_lixo_destino_inadequado_2022",
    "domicilios_improvisados_estrutura_degradada_2022",
    "pct_domicilios_improvisados_estrutura_degradada_2022",
)

DATASETS = {
    "sigesguarda": SilverDataset(
        name="sigesguarda",
        relative_path="sigesguarda/base_unificada.parquet",
        table="silver.sigesguarda_ocorrencias",
        columns=SIGESGUARDA_COLUMNS,
    ),
    "ibge2010": SilverDataset(
        name="ibge2010",
        relative_path="ibge2010/base_bairros_2010.parquet",
        table="silver.ibge_bairros_2010",
        columns=IBGE_2010_COLUMNS,
    ),
    "ibge2022": SilverDataset(
        name="ibge2022",
        relative_path="ibge2022/base_bairros_2022.parquet",
        table="silver.ibge_bairros_2022",
        columns=IBGE_2022_COLUMNS,
    ),
}

def normalize_column_name(column: str) -> str:
    value = unicodedata.normalize("NFKD", column)
    value = value.encode("ascii", "ignore").decode("utf-8")
    value = re.sub(r"[^a-zA-Z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value.lower()

def read_silver_parquet(dataset: SilverDataset) -> pd.DataFrame:
    if not dataset.path.exists():
        raise FileNotFoundError(
            f"Silver Parquet not found for {dataset.name}: {dataset.path}. "
            "Run the silver pipeline before loading PostgreSQL."
        )

    df = pd.read_parquet(dataset.path)
    renamed_columns = [normalize_column_name(column) for column in df.columns]

    if len(renamed_columns) != len(set(renamed_columns)):
        raise ValueError(f"{dataset.name}: duplicate columns after normalization.")

    df.columns = renamed_columns
    validate_columns(df, dataset)
    return cast(pd.DataFrame, df.loc[:, list(dataset.columns)])

def validate_columns(df: pd.DataFrame, dataset: SilverDataset) -> None:
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

        raise ValueError(f"{dataset.name}: invalid silver schema; " + "; ".join(messages))

def to_db_value(value: Any) -> Any:
    if pd.isna(value):
        return None

    if hasattr(value, "item"):
        return value.item()

    return value

def create_load_batch(
    cur: psycopg.Cursor,
    dataset: SilverDataset,
    df: pd.DataFrame,
) -> str:
    cur.execute(
        sql.SQL(
            """
        UPDATE silver.load_batches
        SET is_current = false
        WHERE dataset = %s
        """
        ),
        (dataset.name,),
    )

    cur.execute(
        sql.SQL(
            """
        INSERT INTO silver.load_batches (
            dataset,
            source_path,
            row_count,
            is_current
        )
        VALUES (%s, %s, %s, true)
        RETURNING batch_id
        """
        ),
        (
            dataset.name,
            str(dataset.path),
            len(df),
        ),
    )

    row = cur.fetchone()

    if row is None:
        raise RuntimeError(f"{dataset.name}: failed to create silver load batch.")

    return str(row[0])

def copy_dataframe_to_table(
    cur: psycopg.Cursor,
    dataset: SilverDataset,
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

def load_dataset(conn: psycopg.Connection, dataset: SilverDataset) -> None:
    df = read_silver_parquet(dataset)

    with conn.cursor() as cur:
        batch_id = create_load_batch(cur, dataset, df)

        if not df.empty:
            copy_dataframe_to_table(cur, dataset, batch_id, df)

    print(f"Loaded {len(df)} rows from {dataset.path} into {dataset.table}")

def resolve_datasets(source: str) -> list[SilverDataset]:
    if source == "all":
        return [DATASETS["sigesguarda"], DATASETS["ibge2010"], DATASETS["ibge2022"]]

    if source == "ibge":
        return [DATASETS["ibge2010"], DATASETS["ibge2022"]]

    return [DATASETS[source]]

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load silver Parquet datasets into PostgreSQL."
    )

    parser.add_argument(
        "--source",
        choices=["all", "sigesguarda", "ibge", "ibge2010", "ibge2022"],
        default="all",
        help="Load all silver datasets or only one source.",
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
        for dataset in datasets:
            load_dataset(conn, dataset)

        conn.commit()

if __name__ == "__main__":
    main()
