import argparse
from pathlib import Path

import pandas as pd

from common import (
    BRONZE_DIR,
    CURITIBA_CODIGO_MUNICIPIO,
    aggregate_numeric_table,
    assign_percentages,
    clean_numeric_table,
    filter_by_string_value,
    filter_by_string_values,
    finalize_census_base,
    merge_one_to_one,
    read_csv,
    row_sum,
    safe_pct,
    sum_by,
    var_range,
    write_silver,
)

AJUSTES_IBGE2022 = {
    "botiatuvinha": "butiatuvinha",
    "cidade industrial de curitiba": "cidade industrial",
}

BAIRRO_KEYS = ["CD_BAIRRO", "NM_BAIRRO"]
SALARIO_MINIMO_2022 = 1212

RENDA_RENAME = {
    "V06001": "resp_domicilios_particulares",
    "V06002": "moradores_domicilios_particulares",
    "V06004": "rendimento_medio_responsavel",
}
RENDA_NUMERIC_COLUMNS = list(RENDA_RENAME.values())
RENDA_OUTPUT = [
    "resp_domicilios_particulares",
    "moradores_domicilios_particulares",
    "rendimento_medio_responsavel",
    "rendimento_medio_responsavel_sm",
]

POP_15MAIS = var_range(644, 656, width=5)
ALFABETIZADOS_15MAIS = var_range(748, 760, width=5)
ALFABETIZACAO_COLS = POP_15MAIS + ALFABETIZADOS_15MAIS
ALFABETIZACAO_OUTPUT = [
    "pop_15mais",
    "alfabetizados_15mais",
    "pct_alfabetizacao_15mais",
    "pct_analfabetismo_15mais",
]

DOMICILIO1_VARS = ["V00001", "V00002", "V00052"]
DOMICILIO2_VARS = [
    "V00238",
    "V00312",
    "V00313",
    "V00314",
    "V00316",
    "V00464",
    "V00399",
    "V00400",
    "V00401",
    "V00402",
]
SANEAMENTO_TOTALS = {
    "domicilios_particulares_permanentemente_ocupados_2022": ["V00001"],
    "sem_banheiro_sanitario_2022": ["V00238"],
    "esgotamento_precario_2022": ["V00312", "V00313", "V00314", "V00316"],
    "sem_rede_geral_agua_2022": ["V00464"],
    "lixo_destino_inadequado_2022": ["V00399", "V00400", "V00401", "V00402"],
    "domicilios_improvisados_estrutura_degradada_2022": ["V00002", "V00052"],
}
SANEAMENTO_PERCENTUAIS = {
    "pct_sem_banheiro_sanitario_2022": "sem_banheiro_sanitario_2022",
    "pct_esgotamento_precario_2022": "esgotamento_precario_2022",
    "pct_sem_rede_geral_agua_2022": "sem_rede_geral_agua_2022",
    "pct_lixo_destino_inadequado_2022": "lixo_destino_inadequado_2022",
    "pct_domicilios_improvisados_estrutura_degradada_2022": (
        "domicilios_improvisados_estrutura_degradada_2022"
    ),
}
SANEAMENTO_OUTPUT = [
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
]

def get_context() -> tuple[Path, pd.DataFrame, set[str]]:
    input_dir = BRONZE_DIR / "ibge2022"
    basico = read_csv(input_dir / "Agregados_por_bairros_basico_BR.csv", sep=";")

    curitiba = filter_by_string_value(
        basico,
        "CD_MUN",
        CURITIBA_CODIGO_MUNICIPIO,
        "IBGE 2022 basico",
    )
    bairros_curitiba = set(curitiba["CD_BAIRRO"].astype("string").str.strip())

    return input_dir, curitiba, bairros_curitiba

def read_bairro_file(
    input_dir: Path,
    filename: str,
    bairros_curitiba: set[str],
    variables: list[str],
    context: str,
) -> pd.DataFrame:
    source = read_csv(input_dir / filename, sep=";")
    source = filter_by_string_values(source, "CD_BAIRRO", bairros_curitiba, context)

    return aggregate_numeric_table(
        source,
        BAIRRO_KEYS,
        variables,
        context,
        remove_thousands=True,
    )

def build_population(curitiba: pd.DataFrame) -> pd.DataFrame:
    population = aggregate_numeric_table(
        curitiba,
        BAIRRO_KEYS,
        ["v0001"],
        "IBGE 2022 basico",
        remove_thousands=True,
    ).rename(columns={"v0001": "populacao_2022"})
    population["populacao_2022"] = population["populacao_2022"].astype("Int64")

    return population

def build_income(input_dir: Path, bairros_curitiba: set[str]) -> pd.DataFrame:
    renda = read_csv(input_dir / "Agregados_por_bairros_renda_responsavel_BR.csv", sep=";")
    renda = filter_by_string_values(
        renda,
        "CD_BAIRRO",
        bairros_curitiba,
        "IBGE 2022 renda responsavel",
    ).rename(columns=RENDA_RENAME)

    renda = aggregate_numeric_table(
        renda,
        BAIRRO_KEYS,
        RENDA_NUMERIC_COLUMNS,
        "IBGE 2022 renda responsavel",
        remove_thousands=True,
    )
    renda["rendimento_medio_responsavel_sm"] = (
        renda["rendimento_medio_responsavel"] / SALARIO_MINIMO_2022
    )

    return renda[[*BAIRRO_KEYS, *RENDA_OUTPUT]]

def build_literacy(input_dir: Path, bairros_curitiba: set[str]) -> pd.DataFrame:
    alfabetizacao = read_bairro_file(
        input_dir,
        "Agregados_por_bairros_alfabetizacao_BR.csv",
        bairros_curitiba,
        ALFABETIZACAO_COLS,
        "IBGE 2022 alfabetizacao",
    )

    alfabetizacao["pop_15mais"] = row_sum(alfabetizacao, POP_15MAIS)
    alfabetizacao["alfabetizados_15mais"] = row_sum(alfabetizacao, ALFABETIZADOS_15MAIS)
    alfabetizacao["pct_alfabetizacao_15mais"] = safe_pct(
        alfabetizacao["alfabetizados_15mais"],
        alfabetizacao["pop_15mais"],
    )
    alfabetizacao["analfabetos_15_anos_ou_mais"] = (
        alfabetizacao["pop_15mais"] - alfabetizacao["alfabetizados_15mais"]
    )
    alfabetizacao["pct_analfabetismo_15mais"] = safe_pct(
        alfabetizacao["analfabetos_15_anos_ou_mais"],
        alfabetizacao["pop_15mais"],
    )

    return alfabetizacao[[*BAIRRO_KEYS, *ALFABETIZACAO_OUTPUT]]

def build_sanitation(input_dir: Path, bairros_curitiba: set[str]) -> pd.DataFrame:
    domicilio1 = read_csv(
        input_dir / "Agregados_por_bairros_caracteristicas_domicilio1_BR.csv",
        sep=";",
    )
    domicilio2 = read_csv(
        input_dir / "Agregados_por_bairros_caracteristicas_domicilio2_BR.csv",
        sep=";",
    )

    domicilio1 = filter_by_string_values(
        domicilio1,
        "CD_BAIRRO",
        bairros_curitiba,
        "IBGE 2022 domicilio1",
    )
    domicilio2 = filter_by_string_values(
        domicilio2,
        "CD_BAIRRO",
        bairros_curitiba,
        "IBGE 2022 domicilio2",
    )
    domicilio1 = clean_numeric_table(
        domicilio1,
        BAIRRO_KEYS,
        DOMICILIO1_VARS,
        "IBGE 2022 domicilio1",
        remove_thousands=True,
    )
    domicilio2 = clean_numeric_table(
        domicilio2,
        BAIRRO_KEYS,
        DOMICILIO2_VARS,
        "IBGE 2022 domicilio2",
        remove_thousands=True,
    )

    saneamento = domicilio1[[*BAIRRO_KEYS, *DOMICILIO1_VARS]].merge(
        domicilio2[[*BAIRRO_KEYS, *DOMICILIO2_VARS]],
        on=BAIRRO_KEYS,
        how="inner",
        validate="1:1",
    )
    saneamento = sum_by(saneamento, BAIRRO_KEYS, [*DOMICILIO1_VARS, *DOMICILIO2_VARS])

    for target, columns in SANEAMENTO_TOTALS.items():
        saneamento[target] = row_sum(saneamento, columns)

    saneamento = assign_percentages(
        saneamento,
        "domicilios_particulares_permanentemente_ocupados_2022",
        SANEAMENTO_PERCENTUAIS,
    )

    return saneamento[[*BAIRRO_KEYS, *SANEAMENTO_OUTPUT]]

def build_silver() -> pd.DataFrame:
    input_dir, curitiba, bairros_curitiba = get_context()

    base = merge_one_to_one(
        [
            build_population(curitiba),
            build_income(input_dir, bairros_curitiba),
            build_literacy(input_dir, bairros_curitiba),
            build_sanitation(input_dir, bairros_curitiba),
        ],
        BAIRRO_KEYS,
    )

    return finalize_census_base(
        base,
        name_col="NM_BAIRRO",
        code_col="CD_BAIRRO",
        suffix="2022",
        adjustments=AJUSTES_IBGE2022,
        context="IBGE 2022",
    )

def main() -> None:
    parser = argparse.ArgumentParser(description="Build IBGE 2022 silver dataset.")
    parser.parse_args()

    output_path = write_silver(build_silver(), "ibge2022/base_bairros_2022.parquet")
    print(f"IBGE 2022 silver gerada em {output_path}")


if __name__ == "__main__":
    main()
