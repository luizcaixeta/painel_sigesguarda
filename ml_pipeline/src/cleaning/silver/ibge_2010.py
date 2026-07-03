import argparse
from pathlib import Path

import pandas as pd

from common import (
    BRONZE_DIR,
    CURITIBA_CODIGO_MUNICIPIO,
    aggregate_numeric_table,
    assign_percentages,
    filter_by_string_value,
    finalize_census_base,
    merge_one_to_one,
    read_csv,
    require_columns,
    row_sum,
    safe_pct,
    var_range,
    write_silver,
)

AJUSTES_IBGE2010 = {
    "botiatuvinha": "butiatuvinha",
    "cidade industrial de curitiba": "cidade industrial",
    "alto da rua xv": "alto da xv",
    "campo de santana": "campo do santana",
}

BAIRRO_KEYS = ["Cod_bairro", "Nome_do_bairro"]
SECTOR_KEY = "Cod_setor"
SALARIO_MINIMO_2010 = 510

RENDA_PESSOA_VARS = ["V001", "V002", "V003", "V006", "V007", "V008", "V009", "V010", "V020"]
RENDA_PESSOA_PERCENTUAIS = {
    "pct_sem_rendimento": ["V010"],
    "pct_rendimento_ate_1_sm": ["V001", "V002"],
    "pct_rendimento_ate_2_sm": ["V001", "V002", "V003"],
    "pct_rendimento_acima_5_sm": ["V006", "V007", "V008", "V009"],
}
RENDA_PESSOA_OUTPUT = [
    "pessoas_10_anos_ou_mais",
    "pct_sem_rendimento",
    "pct_rendimento_ate_1_sm",
    "pct_rendimento_ate_2_sm",
    "pct_rendimento_acima_5_sm",
]

RESPONSAVEL_RENDA_VARS = ["V020", "V021", "V022"]
RESPONSAVEL_RENDA_OUTPUT = [
    "resp_domicilios_particulares",
    "rendimento_medio_responsavel",
    "rendimento_medio_responsavel_sm",
]

ALFABETIZADOS_10MAIS = var_range(7, 77)
ALFABETIZADOS_15MAIS = var_range(12, 77)
POP_10MAIS = var_range(50, 134)
POP_15MAIS = var_range(55, 134)
ALFABETIZACAO_COLS = sorted(set(ALFABETIZADOS_10MAIS + ALFABETIZADOS_15MAIS))
IDADE_COLS = sorted(set(POP_10MAIS + POP_15MAIS))
ALFABETIZACAO_TOTALS = {
    "alfabetizados_10mais": ALFABETIZADOS_10MAIS,
    "alfabetizados_15mais": ALFABETIZADOS_15MAIS,
}
IDADE_TOTALS = {
    "pop_10mais": POP_10MAIS,
    "pop_15mais": POP_15MAIS,
}
ALFABETIZACAO_OUTPUT = [
    "pop_10mais",
    "alfabetizados_10mais",
    "pct_alfabetizacao_10mais",
    "pct_analfabetismo_10mais",
    "pop_15mais",
    "alfabetizados_15mais",
    "analfabetos_15mais",
    "pct_alfabetizacao_15mais",
    "pct_analfabetismo_15mais",
]

SANEAMENTO_VARS = [
    "V002",
    "V013",
    "V014",
    "V015",
    "V019",
    "V020",
    "V021",
    "V022",
    "V023",
    "V038",
    "V039",
    "V040",
    "V041",
    "V042",
]
SANEAMENTO_TOTALS = {
    "domicilios_particulares_permanentes": ["V002"],
    "sem_rede_geral_agua": ["V013", "V014", "V015"],
    "sem_banheiro_sanitario": ["V023"],
    "esgotamento_precario": ["V019", "V020", "V021", "V022", "V023"],
    "lixo_destino_inadequado": ["V038", "V039", "V040", "V041", "V042"],
}
SANEAMENTO_PERCENTUAIS = {
    "pct_sem_rede_geral_agua": "sem_rede_geral_agua",
    "pct_sem_banheiro_sanitario": "sem_banheiro_sanitario",
    "pct_esgotamento_precario": "esgotamento_precario",
    "pct_lixo_destino_inadequado": "lixo_destino_inadequado",
}
SANEAMENTO_OUTPUT = [
    "domicilios_particulares_permanentes",
    "sem_rede_geral_agua",
    "pct_sem_rede_geral_agua",
    "sem_banheiro_sanitario",
    "pct_sem_banheiro_sanitario",
    "esgotamento_precario",
    "pct_esgotamento_precario",
    "lixo_destino_inadequado",
    "pct_lixo_destino_inadequado",
]

def get_context() -> tuple[Path, pd.DataFrame, pd.DataFrame]:
    input_dir = BRONZE_DIR / "ibge2010"
    basico = read_csv(input_dir / "Basico_PR.csv", sep=";")

    curitiba = filter_by_string_value(
        basico,
        "Cod_municipio",
        CURITIBA_CODIGO_MUNICIPIO,
        "IBGE 2010 basico",
    )
    require_columns(curitiba, [SECTOR_KEY, *BAIRRO_KEYS], "IBGE 2010 basico")

    setores = (
        curitiba[[SECTOR_KEY, *BAIRRO_KEYS]]
        .dropna(subset=[SECTOR_KEY, "Cod_bairro"])
        .drop_duplicates()
    )

    return input_dir, curitiba, setores

def aggregate_sector_file(
    input_dir: Path,
    filename: str,
    setores: pd.DataFrame,
    variables: list[str],
    context: str,
) -> pd.DataFrame:
    source = read_csv(input_dir / filename, sep=";")
    require_columns(source, [SECTOR_KEY], context)

    source = source.merge(setores, on=SECTOR_KEY, how="inner")
    return aggregate_numeric_table(source, BAIRRO_KEYS, variables, context)

def build_population(curitiba: pd.DataFrame) -> pd.DataFrame:
    population = aggregate_numeric_table(
        curitiba,
        BAIRRO_KEYS,
        ["V002"],
        "IBGE 2010 basico",
    ).rename(columns={"V002": "populacao_2010"})
    population["populacao_2010"] = population["populacao_2010"].astype("Int64")

    return population

def build_income(input_dir: Path, setores: pd.DataFrame) -> pd.DataFrame:
    renda = aggregate_sector_file(
        input_dir,
        "PessoaRenda_PR.csv",
        setores,
        RENDA_PESSOA_VARS,
        "IBGE 2010 PessoaRenda",
    )
    renda["pessoas_10_anos_ou_mais"] = renda["V020"]

    for target, columns in RENDA_PESSOA_PERCENTUAIS.items():
        renda[target] = safe_pct(row_sum(renda, columns), renda["V020"])

    renda = renda[[*BAIRRO_KEYS, *RENDA_PESSOA_OUTPUT]]

    responsavel = aggregate_sector_file(
        input_dir,
        "ResponsavelRenda_PR.csv",
        setores,
        RESPONSAVEL_RENDA_VARS,
        "IBGE 2010 ResponsavelRenda",
    )
    responsavel["resp_domicilios_particulares"] = responsavel["V020"]
    responsavel["rendimento_medio_responsavel"] = (
        responsavel["V022"] / responsavel["V021"].mask(responsavel["V021"] == 0)
    )
    responsavel["rendimento_medio_responsavel_sm"] = (
        responsavel["rendimento_medio_responsavel"] / SALARIO_MINIMO_2010
    )
    responsavel = responsavel[[*BAIRRO_KEYS, *RESPONSAVEL_RENDA_OUTPUT]]

    return merge_one_to_one([renda, responsavel], BAIRRO_KEYS, how="left")

def build_literacy(input_dir: Path, setores: pd.DataFrame) -> pd.DataFrame:
    alfabetizacao = aggregate_sector_file(
        input_dir,
        "Pessoa01_PR.csv",
        setores,
        ALFABETIZACAO_COLS,
        "IBGE 2010 Pessoa01",
    )
    idade = aggregate_sector_file(
        input_dir,
        "Pessoa13_PR.csv",
        setores,
        IDADE_COLS,
        "IBGE 2010 Pessoa13",
    )

    for target, columns in ALFABETIZACAO_TOTALS.items():
        alfabetizacao[target] = row_sum(alfabetizacao, columns)

    for target, columns in IDADE_TOTALS.items():
        idade[target] = row_sum(idade, columns)

    out = merge_one_to_one(
        [
            alfabetizacao[[*BAIRRO_KEYS, *ALFABETIZACAO_TOTALS]],
            idade[[*BAIRRO_KEYS, *IDADE_TOTALS]],
        ],
        BAIRRO_KEYS,
        how="inner",
    )

    out["pct_alfabetizacao_10mais"] = safe_pct(out["alfabetizados_10mais"], out["pop_10mais"])
    out["pct_analfabetismo_10mais"] = 100 - out["pct_alfabetizacao_10mais"]
    out["pct_alfabetizacao_15mais"] = safe_pct(out["alfabetizados_15mais"], out["pop_15mais"])
    out["analfabetos_15mais"] = out["pop_15mais"] - out["alfabetizados_15mais"]
    out["pct_analfabetismo_15mais"] = 100 - out["pct_alfabetizacao_15mais"]

    return out[[*BAIRRO_KEYS, *ALFABETIZACAO_OUTPUT]]

def build_sanitation(input_dir: Path, setores: pd.DataFrame) -> pd.DataFrame:
    saneamento = aggregate_sector_file(
        input_dir,
        "Domicilio01_PR.csv",
        setores,
        SANEAMENTO_VARS,
        "IBGE 2010 Domicilio01",
    )

    for target, columns in SANEAMENTO_TOTALS.items():
        saneamento[target] = row_sum(saneamento, columns)

    saneamento = assign_percentages(
        saneamento,
        "V002",
        SANEAMENTO_PERCENTUAIS,
    )

    return saneamento[[*BAIRRO_KEYS, *SANEAMENTO_OUTPUT]]

def build_silver() -> pd.DataFrame:
    input_dir, curitiba, setores = get_context()

    base = merge_one_to_one(
        [
            build_population(curitiba),
            build_income(input_dir, setores),
            build_literacy(input_dir, setores),
            build_sanitation(input_dir, setores),
        ],
        BAIRRO_KEYS,
    )

    return finalize_census_base(
        base,
        name_col="Nome_do_bairro",
        code_col="Cod_bairro",
        suffix="2010",
        adjustments=AJUSTES_IBGE2010,
        context="IBGE 2010",
    )

def main() -> None:
    parser = argparse.ArgumentParser(description="Build IBGE 2010 silver dataset.")
    parser.parse_args()

    output_path = write_silver(build_silver(), "ibge2010/base_bairros_2010.parquet")
    print(f"IBGE 2010 silver gerada em {output_path}")


if __name__ == "__main__":
    main()
