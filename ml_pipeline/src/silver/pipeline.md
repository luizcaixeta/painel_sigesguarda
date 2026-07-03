```text
                              ┌──────────────────────────────┐
                              │ run.py --source all | fonte  │
                              └───────────────┬──────────────┘
                                              │
                 ┌────────────────────────────┼────────────────────────────┐
                 ↓                            ↓                            ↓
┌─────────────────────────────┐ ┌─────────────────────────────┐ ┌─────────────────────────────┐
│ ibge_2010.build_silver()    │ │ ibge_2022.build_silver()    │ │ sigesguarda.build_silver()  │
└──────────────┬──────────────┘ └──────────────┬──────────────┘ └──────────────┬──────────────┘
               │                               │                               │
               ↓                               ↓                               ↓
┌─────────────────────────────┐ ┌─────────────────────────────┐ ┌─────────────────────────────┐
│ Bronze IBGE 2010            │ │ Bronze IBGE 2022            │ │ Bronze SIGESGUARDA          │
│ data/bronze/ibge2010        │ │ data/bronze/ibge2022        │ │ data/bronze/sigesguarda     │
└──────────────┬──────────────┘ └──────────────┬──────────────┘ └──────────────┬──────────────┘
               │                               │                               │
               ↓                               ↓                               ↓
┌─────────────────────────────┐ ┌─────────────────────────────┐ ┌─────────────────────────────┐
│ Recorte Curitiba            │ │ Recorte Curitiba            │ │ Unificacao historica+atual  │
│ Cod_municipio = 4106902     │ │ CD_MUN = 4106902            │ │ datas, concat e dedup       │
└──────────────┬──────────────┘ └──────────────┬──────────────┘ └──────────────┬──────────────┘
               │                               │                               │
               ↓                               ↓                               ↓
┌─────────────────────────────┐ ┌─────────────────────────────┐ ┌─────────────────────────────┐
│ Agrega por bairro           │ │ Agrega por bairro           │ │ Limpa ocorrencias           │
│ setores -> bairros          │ │                             │ │ texto, bairro, tempo, flags │
└──────────────┬──────────────┘ └──────────────┬──────────────┘ └──────────────┬──────────────┘
               │                               │                               │
               └───────────────┬───────────────┴───────────────┬───────────────┘
                               ↓                               ↓
                    ┌──────────────────────┐      ┌──────────────────────────┐
                    │ Validacoes comuns    │      │ Escrita silver parquet   │
                    │ bairros oficiais     │─────▶│ data/silver/...          │
                    └──────────────────────┘      └──────────────────────────┘
```

## IBGE 2010

```text
                         ┌──────────────────────────────┐
                         │ data/bronze/ibge2010         │
                         └───────────────┬──────────────┘
                                         │
                                         ↓
                         ┌──────────────────────────────┐
                         │ Basico_PR.csv                │
                         │ filtra Cod_municipio 4106902 │
                         └───────────────┬──────────────┘
                                         │
                                         ↓
                         ┌──────────────────────────────┐
                         │ Contexto territorial         │
                         │ Cod_setor + Cod_bairro       │
                         │ Nome_do_bairro               │
                         └───────────────┬──────────────┘
                                         │
       ┌─────────────────────────────────┼─────────────────────────────────┐
       ↓                                 ↓                                 ↓
┌──────────────────┐           ┌──────────────────────┐          ┌──────────────────────┐
│ Populacao        │           │ Renda                │          │ Alfabetizacao        │
│ Basico_PR V002   │           │ PessoaRenda +        │          │ Pessoa01 + Pessoa13  │
└────────┬─────────┘           │ ResponsavelRenda     │          └──────────┬───────────┘
         │                     └──────────┬───────────┘                     │
         │                                │                                 │
         │                                ↓                                 │
         │                     ┌──────────────────────┐                     │
         │                     │ Limpeza numerica     │                     │
         │                     │ totais, percentuais  │                     │
         │                     │ renda em salario min │                     │
         │                     └──────────┬───────────┘                     │
         │                                │                                 │
         └────────────────────┬───────────┴─────────────────────┬───────────┘
                              ↓                                 ↓
                    ┌──────────────────────┐          ┌──────────────────────┐
                    │ Saneamento           │          │ merge_one_to_one     │
                    │ Domicilio01          │─────────▶│ chaves de bairro     │
                    │ totais e percentuais │          └──────────┬───────────┘
                    └──────────────────────┘                     │
                                                                 ↓
                                                   ┌──────────────────────────┐
                                                   │ finalize_census_base     │
                                                   │ limpa nome de bairro     │
                                                   │ aplica ajustes 2010      │
                                                   │ remove Cod_bairro        │
                                                   │ sufixo _2010             │
                                                   │ valida bairros oficiais  │
                                                   └────────────┬─────────────┘
                                                                ↓
                                                   ┌──────────────────────────┐
                                                   │ data/silver/ibge2010/    │
                                                   │ base_bairros_2010.parquet│
                                                   └──────────────────────────┘
```

## IBGE 2022

```text
                         ┌──────────────────────────────┐
                         │ data/bronze/ibge2022         │
                         └───────────────┬──────────────┘
                                         │
                                         ↓
                         ┌──────────────────────────────┐
                         │ Agregados_por_bairros_       │
                         │ basico_BR.csv                │
                         │ filtra CD_MUN 4106902        │
                         └───────────────┬──────────────┘
                                         │
                                         ↓
                         ┌──────────────────────────────┐
                         │ Lista bairros Curitiba       │
                         │ CD_BAIRRO + NM_BAIRRO        │
                         └───────────────┬──────────────┘
                                         │
       ┌─────────────────────────────────┼─────────────────────────────────┐
       ↓                                 ↓                                 ↓
┌──────────────────────┐       ┌──────────────────────┐          ┌──────────────────────┐
│ Populacao            │       │ Renda responsavel    │          │ Alfabetizacao        │
│ basico v0001         │       │ renomeia variaveis   │          │ soma faixas 15+      │
└──────────┬───────────┘       └──────────┬───────────┘          └──────────┬───────────┘
           │                              │                                 │
           │                              ↓                                 │
           │                   ┌──────────────────────┐                     │
           │                   │ Limpeza numerica     │                     │
           │                   │ remove milhares      │                     │
           │                   │ salario minimo 2022  │                     │
           │                   └──────────┬───────────┘                     │
           │                              │                                 │
           └──────────────────┬───────────┴─────────────────────┬───────────┘
                              ↓                                 ↓
                    ┌──────────────────────┐          ┌──────────────────────┐
                    │ Saneamento           │          │ merge_one_to_one     │
                    │ domicilio1 +         │─────────▶│ chaves de bairro     │
                    │ domicilio2           │          └──────────┬───────────┘
                    │ totais e percentuais │                     │
                    └──────────────────────┘                     ↓
                                                   ┌──────────────────────────┐
                                                   │ finalize_census_base     │
                                                   │ limpa nome de bairro     │
                                                   │ aplica ajustes 2022      │
                                                   │ remove CD_BAIRRO         │
                                                   │ sufixo _2022             │
                                                   │ valida bairros oficiais  │
                                                   └────────────┬─────────────┘
                                                                ↓
                                                   ┌──────────────────────────┐
                                                   │ data/silver/ibge2022/    │
                                                   │ base_bairros_2022.parquet│
                                                   └──────────────────────────┘
```

## SIGESGUARDA

```text
                         ┌──────────────────────────────┐
                         │ data/bronze/sigesguarda      │
                         └───────────────┬──────────────┘
                                         │
                 ┌───────────────────────┼──────────────────────┐
                 ↓                       ↓                      │
     ┌──────────────────────┐ ┌──────────────────────┐          │
     │ Base historica       │ │ Arquivo atual        │          │
     │ 2024-02-01_...csv    │ │ latest_current_file  │          │
     └──────────┬───────────┘ └──────────┬───────────┘          │
                │                        │                      │
                ↓                        ↓                      │
     ┌──────────────────────┐ ┌──────────────────────┐          │
     │ Parse data historica │ │ Parse data atual     │          │
     │ %Y-%m-%d %H:%M:%S    │ │ %d/%m/%Y             │          │
     │ ano, mes, dia        │ │ ano, mes, dia        │          │
     └──────────┬───────────┘ └──────────┬───────────┘          │
                └────────────┬───────────┘                      │
                             ↓                                  │
                   ┌──────────────────────┐                     │
                   │ Concatena bases      │                     │
                   │ remove ATENDIMENTO_  │                     │
                   │ ANO quando existir   │                     │
                   └──────────┬───────────┘                     │
                              ↓                                 │
                   ┌──────────────────────┐                     │
                   │ Remove duplicidade   │                     │
                   │ OCORRENCIA_CODIGO    │                     │
                   │ mantendo ultimo      │                     │
                   └──────────┬───────────┘                     │
                              ↓                                 │
             ┌────────────────┼────────────────┐                │
             ↓                ↓                ↓                ↓
┌────────────────────┐ ┌────────────────┐ ┌────────────────┐ ┌────────────────────┐
│ Limpa texto        │ │ Padroniza      │ │ Mapeia flags   │ │ Dia e horario      │
│ lower, acento,     │ │ bairro         │ │ binarias para  │ │ dia semana -> cod  │
│ pontuacao, espacos │ │ MAPA_BAIRRO    │ │ 0/1 Int64      │ │ hora/minuto        │
└─────────┬──────────┘ │ descarta NA,   │ └───────┬────────┘ │ periodos do dia    │
          │            │ RM e invalidos │         │          └─────────┬──────────┘
          │            └────────┬───────┘         │                    │
          └─────────────────────┼─────────────────┴────────────────────┘
                                ↓
                   ┌──────────────────────────┐
                   │ Natureza da ocorrencia   │
                   │ limpa NATUREZA1..5       │
                   │ aplica CORRECOES         │
                   │ remove indeterminadas    │
                   │ classifica 1 categoria   │
                   └────────────┬─────────────┘
                                ↓
                   ┌──────────────────────────┐
                   │ Pos-limpeza              │
                   │ remove colunas default   │
                   │ valida bairros oficiais  │
                   │ garante 1 flag natureza  │
                   └────────────┬─────────────┘
                                ↓
                   ┌──────────────────────────┐
                   │ data/silver/sigesguarda/ │
                   │ base_unificada.parquet   │
                   └──────────────────────────┘
```
