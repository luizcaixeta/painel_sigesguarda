# Pipeline Bronze

```text
                         ┌──────────────────────────────────┐
                         │ Fontes publicas                  │
                         │ SIGESGUARDA + IBGE 2010/2022     │
                         └────────────────┬─────────────────┘
                                          │
             ┌────────────────────────────┼────────────────────────────┐
             ↓                            ↓                            ↓
┌─────────────────────────┐  ┌─────────────────────────┐  ┌─────────────────────────┐
│ download_sigesguarda.py │  │ download_ibge_2010.py   │  │ download_ibge_2022.py   │
└────────────┬────────────┘  └────────────┬────────────┘  └────────────┬────────────┘
             │                            │                            │
             ↓                            ↓                            ↓
┌─────────────────────────┐  ┌─────────────────────────┐  ┌─────────────────────────┐
│ data/bronze/            │  │ data/bronze/ibge2010    │  │ data/bronze/ibge2022    │
│ sigesguarda             │  │ 6 CSVs necessarios      │  │ 5 CSVs necessarios      │
└────────────┬────────────┘  └────────────┬────────────┘  └────────────┬────────────┘
             └────────────────────────────┼────────────────────────────┘
                                          │
                                          ↓
                         ┌──────────────────────────────────┐
                         │ load_raw_to_postgres.py          │
                         │ --source fonte | todas as fontes │
                         └────────────────┬─────────────────┘
                                          │
                         ┌────────────────┴─────────────────┐
                         ↓                                  ↓
              ┌──────────────────────┐           ┌──────────────────────┐
              │ bronze.raw_files     │           │ bronze.raw_records   │
              │ metadados do arquivo │──────────▶│ linha original JSONB │
              └──────────────────────┘           └──────────────────────┘
```

## SIGESGUARDA

```text
                    ┌────────────────────────────────┐
                    │ Portal de Dados Abertos        │
                    │ Prefeitura de Curitiba         │
                    └───────────────┬────────────────┘
                                    │
                                    ↓
                    ┌────────────────────────────────┐
                    │ Consulta lista de arquivos     │
                    │ pagina 1, ate 50 resultados    │
                    └───────────────┬────────────────┘
                                    │
                                    ↓
                    ┌────────────────────────────────┐
                    │ Filtra CSVs do SIGESGUARDA     │
                    │ seleciona atualizacao mais nova│
                    └───────────────┬────────────────┘
                                    │
                    ┌───────────────┴────────────────┐
                    ↓                                ↓
       ┌────────────────────────┐       ┌────────────────────────┐
       │ --check-only           │       │ Compara metadados com  │
       │ informa se ha novidade │       │ download_state.json    │
       └────────────────────────┘       └────────────┬───────────┘
                                                     │ arquivo novo
                                                     ↓
                                       ┌────────────────────────┐
                                       │ Baixa base historica   │
                                       │ e arquivo atual        │
                                       │ via arquivo .tmp       │
                                       └────────────┬───────────┘
                                                    │
                                                    ↓
                                       ┌────────────────────────┐
                                       │ Remove versoes antigas │
                                       │ preserva historico,    │
                                       └────────────┬───────────┘
                                                    │
                                                    ↓
                                       ┌────────────────────────┐
                                       │ Salva metadados        │
                                       │ download_state.json    │
                                       └────────────┬───────────┘
                                                    │
                                                    ↓
                                       ┌────────────────────────┐
                                       │ data/bronze/           │
                                       │ sigesguarda/*.csv      │
                                       └────────────────────────┘
```

## IBGE 2010

```text
                    ┌────────────────────────────────┐
                    │ FTP IBGE                       │
                    │ agregados por setores do PR    │
                    └───────────────┬────────────────┘
                                    │
                                    ↓
                    ┌────────────────────────────────┐
                    │ Baixa censo2010_pr.zip         │
                    │ ignora se ja existir           │
                    └───────────────┬────────────────┘
                                    │
                                    ↓
                    ┌────────────────────────────────┐
                    │ Extrai ZIP                     │
                    │ remove o arquivo compactado    │
                    └───────────────┬────────────────┘
                                    │
                                    ↓
                    ┌────────────────────────────────┐
                    │ Move CSVs para a raiz Bronze   │
                    │ remove diretorio extraido      │
                    └───────────────┬────────────────┘
                                    │
                                    ↓
                    ┌────────────────────────────────┐
                    │ Mantem somente 6 arquivos      │
                    │ Basico, renda, alfabetizacao   │
                    │ e domicilio                    │
                    └───────────────┬────────────────┘
                                    │
                                    ↓
                    ┌────────────────────────────────┐
                    │ data/bronze/ibge2010/*.csv     │
                    └────────────────────────────────┘
```

Arquivos preservados:

- `Basico_PR.csv`
- `PessoaRenda_PR.csv`
- `ResponsavelRenda_PR.csv`
- `Pessoa01_PR.csv`
- `Pessoa13_PR.csv`
- `Domicilio01_PR.csv`

## IBGE 2022

```text
                    ┌────────────────────────────────┐
                    │ FTP IBGE                       │
                    │ agregados por bairros do Brasil│
                    └───────────────┬────────────────┘
                                    │
                                    ↓
                    ┌────────────────────────────────┐
                    │ Baixa 5 arquivos ZIP           │
                    │ ignora os que ja existem       │
                    └───────────────┬────────────────┘
                                    │
                                    ↓
                    ┌────────────────────────────────┐
                    │ Extrai cada ZIP em sua pasta   │
                    │ remove arquivos compactados    │
                    └───────────────┬────────────────┘
                                    │
                                    ↓
                    ┌────────────────────────────────┐
                    │ Localiza CSVs recursivamente   │
                    │ move os necessarios para raiz  │
                    └───────────────┬────────────────┘
                                    │
                                    ↓
                    ┌────────────────────────────────┐
                    │ Remove pastas e arquivos extras│
                    │ mantem somente os 5 datasets   │
                    └───────────────┬────────────────┘
                                    │
                                    ↓
                    ┌────────────────────────────────┐
                    │ data/bronze/ibge2022/*.csv     │
                    └────────────────────────────────┘
```

São preservados os agregados de dados básicos, alfabetização, renda do
responsável e as duas bases de características dos domicílios.

## Carga no PostgreSQL

```text
                    ┌────────────────────────────────┐
                    │ data/bronze/*/*.csv            │
                    │ --source limita uma fonte      │
                    └───────────────┬────────────────┘
                                    │
                                    ↓
                    ┌────────────────────────────────┐
                    │ Detecta delimitador ; ou ,     │
                    │ leitura latin1                 │
                    └───────────────┬────────────────┘
                                    │
                                    ↓
                    ┌────────────────────────────────┐
                    │ Upsert bronze.raw_files        │
                    │ caminho, tamanho e loaded_at   │
                    └───────────────┬────────────────┘
                                    │
                                    ↓
                    ┌────────────────────────────────┐
                    │ Remove registros anteriores   │
                    │ vinculados ao mesmo arquivo    │
                    └───────────────┬────────────────┘
                                    │
                                    ↓
                    ┌────────────────────────────────┐
                    │ DictReader linha a linha       │
                    │ payload original como JSONB    │
                    └───────────────┬────────────────┘
                                    │
                                    ↓
                    ┌────────────────────────────────┐
                    │ bronze.raw_records             │
                    │ source + row_number + payload  │
                    └────────────────────────────────┘
```

A carga é reexecutável por arquivo: os metadados são atualizados e os registros
anteriores daquele arquivo são substituídos dentro da mesma transação.
