# Pipeline Gold

```text
                              ┌──────────────────────────────┐
                              │ run.py                       │
                              │ --source all | ml_features   │
                              └───────────────┬──────────────┘
                                              │
                                              ↓
                              ┌──────────────────────────────┐
                              │ ml_features.build_gold()     │
                              └───────────────┬──────────────┘
                                              │
                 ┌────────────────────────────┼────────────────────────────┐
                 ↓                            ↓                            ↓
┌─────────────────────────────┐ ┌─────────────────────────────┐ ┌─────────────────────────────┐
│ Silver SIGESGUARDA          │ │ Silver IBGE 2010            │ │ Silver IBGE 2022            │
│ base_unificada.parquet      │ │ base_bairros_2010.parquet   │ │ base_bairros_2022.parquet   │
└──────────────┬──────────────┘ └──────────────┬──────────────┘ └──────────────┬──────────────┘
               │                               │                               │
               ↓                               └───────────────┬───────────────┘
┌─────────────────────────────┐                                 ↓
│ Painel mensal de ocorrencias│                  ┌─────────────────────────────┐
│ bairro x mes x categoria    │                  │ Estimativas socioeconomicas │ 
└──────────────┬──────────────┘                  │ bairro x ano                │
               │                                 └──────────────┬──────────────┘
               └───────────────────────────────┬────────────────┘
                                               ↓
                              ┌──────────────────────────────┐
                              │ Merge bairro + ano           │
                              │ valida cobertura completa    │
                              └───────────────┬──────────────┘
                                              │
                                              ↓
                              ┌───────────────────────────────┐
                              │ Features temporais e sazonais │
                              │ schema final sem valores nulos│
                              └────────────────┬──────────────┘
                                              │
                                              ↓
                              ┌──────────────────────────────┐
                              │ data/gold/ml_features/       │
                              │ ocorrencias_mensais.parquet  │
                              └──────────────────────────────┘
```

## Painel mensal de ocorrências

```text
                    ┌────────────────────────────────┐
                    │ Silver SIGESGUARDA             │
                    │ bairro + ano + mes + categorias│
                    └───────────────┬────────────────┘
                                    │
                                    ↓
                    ┌────────────────────────────────┐
                    │ Seleciona 6 categorias         │
                    │ e converte flags para inteiros │
                    └───────────────┬────────────────┘
                                    │
                                    ↓
                    ┌────────────────────────────────┐
                    │ Converte formato largo -> longo│
                    │ uma linha por categoria        │
                    └───────────────┬────────────────┘
                                    │
                                    ↓
                    ┌────────────────────────────────┐
                    │ Soma ocorrencias por           │
                    │ bairro + mes + categoria       │
                    └───────────────┬────────────────┘
                                    │
                                    ↓
                    ┌────────────────────────────────┐
                    │ Produto cartesiano completo    │
                    │ bairros x meses x categorias   │
                    └───────────────┬────────────────┘
                                    │
                                    ↓
                    ┌────────────────────────────────┐
                    │ Meses sem ocorrencia recebem 0 │
                    │ cria ano, mes e tempo          │
                    └────────────────────────────────┘
```

Categorias modeladas:

- `ACIDENTE_TRANSITO`
- `ATENDIMENTO_OPERACIONAL_ASSISTENCIAL`
- `CRIME_PATRIMONIAL`
- `CRIME_VIOLENTO`
- `CRIME_ORDEM_PUBLICA`
- `CRIME_DROGAS_SUBSTANCIAS`

## Indicadores socioeconômicos

```text
        ┌──────────────────────────┐       ┌──────────────────────────┐
        │ IBGE Silver 2010         │       │ IBGE Silver 2022         │
        │ indicadores por bairro   │       │ indicadores por bairro   │
        └────────────┬─────────────┘       └────────────┬─────────────┘
                     └──────────────────┬───────────────┘
                                        ↓
                         ┌──────────────────────────────┐
                         │ Merge one-to-one por bairro  │
                         │ valida colunas obrigatorias  │
                         └───────────────┬──────────────┘
                                         │
                                         ↓
                         ┌──────────────────────────────┐
                         │ Expande bairro x anos        │
                         │ presentes nas ocorrencias    │
                         └───────────────┬──────────────┘
                                         │
                                         ↓
                         ┌──────────────────────────────┐
                         │ Estimativa linear 2010-2022  │
                         │ observado nos anos censais   │
                         │ interpolado entre os censos  │
                         │ extrapolado fora do intervalo│
                         └───────────────┬──────────────┘
                                         │
                         ┌───────────────┴───────────────┐
                         ↓                               ↓
          ┌──────────────────────────┐    ┌──────────────────────────┐
          │ Alfabetizacao            │    │ Saneamento               │
          │ totais e percentuais     │    │ limites e percentuais    │
          └────────────┬─────────────┘    └────────────┬─────────────┘
                       └───────────────┬───────────────┘
                                       ↓
                         ┌──────────────────────────────┐
                         │ IQV ponderado                │
                         │ renda + alfabetizacao +      │
                         │ quatro indicadores sanitarios│
                         └───────────────┬──────────────┘
                                         │
                                         ↓
                         ┌──────────────────────────────┐
                         │ populacao_estimada           │
                         │ log_pop + iqv                │
                         │ tipo_estimativa              │
                         └──────────────────────────────┘
```

O IQV atribui um terço do peso à renda, um terço à alfabetização e divide o
terço restante igualmente entre ausência de banheiro, esgotamento precário,
ausência de rede geral de água e destino inadequado do lixo. Nos indicadores
de precariedade, valores menores recebem uma avaliação melhor.

## Feature engineering temporal

```text
                    ┌────────────────────────────────┐
                    │ Painel mensal + socioeconomia  │
                    │ merge por bairro e ano         │
                    └───────────────┬────────────────┘
                                    │
                                    ↓
                    ┌────────────────────────────────┐
                    │ Ordena por                     │
                    │ bairro + categoria + data      │
                    └───────────────┬────────────────┘
                                    │
               ┌────────────────────┼────────────────────┐
               ↓                    ↓                    ↓
    ┌────────────────────┐ ┌────────────────────┐ ┌────────────────────┐
    │ Lags               │ │ Medias moveis      │ │ Media historica    │
    │ 1, 2, 3, 6, 12     │ │ 3, 6 e 12 meses    │ │ expansiva          │
    └──────────┬─────────┘ └──────────┬─────────┘ └──────────┬─────────┘
               └──────────────────────┼──────────────────────┘
                                      │
                                      ↓
                    ┌────────────────────────────────┐
                    │ Usa apenas o passado           │
                    │ shift(1) evita vazamento de y  │
                    └───────────────┬────────────────┘
                                    │
                                    ↓
                    ┌────────────────────────────────┐
                    │ Remove linhas sem todos os lags│
                    │ aplica log1p nas features      │
                    └───────────────┬────────────────┘
                                    │
                                    ↓
                    ┌────────────────────────────────┐
                    │ Sazonalidade mensal            │
                    │ seno/cosseno harmonicos 1 e 2  │
                    └───────────────┬────────────────┘
                                    │
                                    ↓
                    ┌────────────────────────────────┐
                    │ Tipagem final e validacao      │
                    │ 32 colunas, nenhum valor nulo  │
                    └────────────────────────────────┘
```

## Carga no PostgreSQL

```text
                    ┌────────────────────────────────┐
                    │ load_gold_to_postgres.py       │
                    │ --source all | ml_features     │
                    └───────────────┬────────────────┘
                                    │
                                    ↓
                    ┌────────────────────────────────┐
                    │ Le Parquet Gold                │
                    │ valida colunas exatas          │
                    └───────────────┬────────────────┘
                                    │
                                    ↓
                    ┌────────────────────────────────┐
                    │ Desativa lote corrente anterior│
                    │ cria gold.load_batches         │
                    └───────────────┬────────────────┘
                                    │
                                    ↓
                    ┌────────────────────────────────┐
                    │ PostgreSQL COPY FROM STDIN     │
                    │ batch_id + source_row_number   │
                    └───────────────┬────────────────┘
                                    │
                                    ↓
                    ┌────────────────────────────────┐
                    │ gold.ocorrencias_mensais_      │
                    │ ml_features                    │
                    └────────────────────────────────┘
```

A carga registra caminho, quantidade de linhas e horário de cada lote. A
restrição de lote corrente garante que exista somente uma versão ativa do
dataset `ml_features`.
