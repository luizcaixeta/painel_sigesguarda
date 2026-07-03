# Transformacoes Para a Camada Silver

Este documento consolida as limpezas e transformacoes identificadas em `data_analysis/src` para orientar a implementacao da camada silver a partir das bases bronze.

## Escopo

Fontes analisadas:

- SIGESGUARDA: `data_analysis/src/01 - sigesguarda/01_configurando_base_de_dados.ipynb` e `02_limpeza_dos_dados.ipynb`
- IBGE Censo 2010: `data_analysis/src/02 - ibge2010/01_configurando_base_de_dados.ipynb`
- IBGE Censo 2022: `data_analysis/src/03 - ibge2022/01_configurando_base_de_dados.ipynb`

Arquivos de configuracao usados pelas limpezas:

- `data_analysis/config/data_cleaning_config.py`
- `data_analysis/config/bairro_cleaning_config.py`
- `data_analysis/config/natureza_descricao_cleaning_config.py`

## Padroes comuns

### Normalizacao de texto

Aplicada principalmente em SIGESGUARDA e reutilizada nas bases do IBGE para nomes de bairros.

- Valores nulos permanecem como `pd.NA`.
- Conversao para string.
- Remocao de espacos no inicio e no fim.
- Conversao para letras minusculas.
- Remocao de acentos via normalizacao Unicode `NFKD` e codificacao ASCII.
- Substituicao de caracteres especiais por espaco, mantendo apenas letras, numeros e espacos.
- Colapso de multiplos espacos para um unico espaco.
- Strings vazias apos limpeza viram `pd.NA`.

### Padronizacao de bairros

Usada para tornar SIGESGUARDA e IBGE comparaveis pela chave `ATENDIMENTO_BAIRRO_NOME`.

- Limpeza textual dos nomes de bairro.
- Descarte de valores sem localizacao valida, como `bairro ficticio`, `nao informado`, `sem dados`, `nf` e `ni`.
- Descarte de bairros/regioes fora do municipio de Curitiba, listados como regiao metropolitana.
- Correcao de erros de digitacao e abreviacoes por `MAPA_BAIRRO`, por exemplo:
  - `centro cavico` -> `centro civico`
  - `alto da gla3ria` -> `alto da gloria`
  - `cic` -> `cidade industrial`
  - `campo de santana` -> `campo do santana`
- Validacao final contra a lista de bairros oficiais de Curitiba.
- Registros sem bairro valido sao descartados na SIGESGUARDA.

### Conversao numerica

Padrao recorrente nos censos:

- Leitura inicial dos arquivos como texto.
- Remocao de espacos.
- Conversao de marcadores invalidos ou ausentes (`X`, string vazia e `nan`) para nulo.
- Ajuste de separador decimal, trocando virgula por ponto.
- Em arquivos de 2022, remocao de ponto usado como separador de milhar antes da conversao.
- Conversao com `pd.to_numeric(..., errors="coerce")`.

## SIGESGUARDA

### Entrada e consolidacao

Arquivos usados:

- `data/sigesguarda/raw/2024-02-01_sigesguarda_-_Base_de_Dados.csv`
- `data/sigesguarda/raw/2026-04-02_sigesguarda_-_Base_de_Dados.csv`

Saida atual dos notebooks:

- `data/sigesguarda/base_de_dados/base_unificada.csv`
- `data/sigesguarda/cleaned/base_unificada.csv`

Transformacoes identificadas:

- Leitura da base antiga com separador `;` e encoding `latin1`.
- Leitura da base atual com separador `,` e encoding `latin1`.
- Remocao de uma primeira linha invalida na base antiga, identificada como marcador/estilo e nao como registro de ocorrencia.
- Validacao do formato de `OCORRENCIA_DATA`:
  - base antiga: formato `ano-mes-dia hora:minuto:segundo.000`
  - base atual: formato `dia/mes/ano`
- Conversao de `OCORRENCIA_DATA` em tres colunas inteiras:
  - `OCORRENCIA_ANO`
  - `OCORRENCIA_MES`
  - `OCORRENCIA_DIA`
- Remocao da coluna original `OCORRENCIA_DATA` apos a separacao.
- Remocao de `ATENDIMENTO_ANO`, por ser redundante com `OCORRENCIA_ANO`.
- Recorte das duas bases em novembro de 2022 para verificacao de codigos em comum por `OCORRENCIA_CODIGO`.
- Concatenacao vertical da base antiga com a base atual.

### Limpeza textual

Colunas textuais configuradas:

- `ATENDIMENTO_BAIRRO_NOME`
- `LOGRADOURO_NOME`
- `NATUREZA1_DESCRICAO`
- `NATUREZA2_DESCRICAO`
- `NATUREZA3_DESCRICAO`
- `NATUREZA4_DESCRICAO`
- `NATUREZA5_DESCRICAO`
- `SECRETARIA_SIGLA`
- `SERVICO_NOME`
- `NUMERO_PROTOCOLO_156`

Transformacoes:

- Aplicacao da funcao padrao de limpeza textual.
- Padronizacao especifica de `ATENDIMENTO_BAIRRO_NOME`.
- Descarte de linhas com bairro nulo apos padronizacao.

### Colunas binarias

Colunas configuradas:

- `FLAG_EQUIPAMENTO_URBANO`
- `FLAG_FLAGRANTE`
- `NATUREZA1_DEFESA_CIVIL`
- `NATUREZA2_DEFESA_CIVIL`
- `NATUREZA3_DEFESA_CIVIL`
- `NATUREZA4_DEFESA_CIVIL`
- `NATUREZA5_DEFESA_CIVIL`

Transformacoes:

- Conversao de valores positivos (`sim`, `y`, `t`, `1`, `1.0`) para `1`.
- Conversao de valores negativos, ausentes, tracados ou nao reconhecidos para `0`.
- Tipagem final como inteiro anulavel `Int64`.

### Dia da semana

Transformacoes em `OCORRENCIA_DIA_SEMANA`:

- Limpeza textual.
- Mapeamento para inteiro:
  - `domingo` = 1
  - `segunda` = 2
  - `terca` = 3
  - `quarta` = 4
  - `quinta` = 5
  - `sexta` = 6
  - `sabado` = 7
- Valores nulos ou nao mapeados recebem `0`.
- Tipagem final como `Int64`.

### Hora e periodo do dia

Transformacoes em `OCORRENCIA_HORA`:

- Interpretacao do horario no formato `HH:MM:SS`.
- Criacao de:
  - `OCORRENCIA_HORA_HORA`
  - `OCORRENCIA_HORA_MINUTO`
- Descarte da coluna original `OCORRENCIA_HORA`.
- Criacao de flags de periodo:
  - `MADRUGADA`: hora entre 0 e 5
  - `MANHA`: hora entre 6 e 11
  - `TARDE`: hora entre 12 e 17
  - `NOITE`: hora entre 18 e 23

### Natureza da ocorrencia

Colunas usadas:

- `NATUREZA1_DESCRICAO`
- `NATUREZA2_DESCRICAO`
- `NATUREZA3_DESCRICAO`
- `NATUREZA4_DESCRICAO`
- `NATUREZA5_DESCRICAO`

Transformacoes:

- Limpeza textual das colunas de natureza.
- Correcao de erros de digitacao por `CORRECOES`, por exemplo:
  - `ameaaa` -> `ameaca`
  - `perseguiaao stalking` -> `perseguicao stalking`
  - `substancia ilacita` -> `substancia ilicita`
  - `homicadio` -> `homicidio`
- Descarte de linhas sem nenhuma natureza preenchida.
- Descarte de linhas com natureza indeterminada `tentativa`.
- Construcao de mapa reverso natureza -> categoria.
- Validacao para impedir que uma mesma natureza pertenca a mais de uma categoria.
- Classificacao de cada linha pela primeira categoria encontrada entre as colunas de natureza.
- Criacao de flags booleanas exclusivas, uma por categoria:
  - `CRIME_VIOLENTO`
  - `ATENDIMENTO_OPERACIONAL_ASSISTENCIAL`
  - `ACIDENTE_TRANSITO`
  - `ACIDENTE_NATURAL`
  - `CRIME_PATRIMONIAL`
  - `CRIME_ADMNISTRACAO_PUBLICA`
  - `CRIME_HONRA_DISCRIMINACAO`
  - `CRIME_CRIANCA_ADOLESCENTE`
  - `CRIME_FRAUDE_DOCUMENTAL`
  - `CRIME_DROGAS_SUBSTANCIAS`
  - `CRIME_ORDEM_PUBLICA`
  - `RISCO_ESTRUTURAL`
  - `EXPLOSIVOS_E_PRODUTOS_PERIGOSOS`
  - `PESSOAS_DESAPARECIDAS`
  - `MATERIAIS_OBJETOS`
- Validacao de que cada registro ficou em exatamente uma categoria.

### Colunas removidas

Colunas configuradas para descarte quando presentes:

- `OCORRENCIA_CODIGO`
- `REGIONAL_FATO_NOME`
- `SECRETARIA_NOME`
- `SITUACAO_EQUIPE_DESCRICAO`
- `OCORRENCIA_DATA`
- `OPERACAO_DESCRICAO`
- `ORIGEM_CHAMADO_DESCRICAO`
- `SUBCATEGORIA1_DESCRICAO`
- `SUBCATEGORIA2_DESCRICAO`
- `SUBCATEGORIA3_DESCRICAO`
- `SUBCATEGORIA4_DESCRICAO`
- `SUBCATEGORIA5_DESCRICAO`
- `EQUIPAMENTO_URBANO_NOME`

## IBGE Censo 2010

### Entrada e granularidade

Arquivos usados:

- `Basico_PR.csv`
- `PessoaRenda_PR.csv`
- `ResponsavelRenda_PR.csv`
- `Pessoa01_PR.csv`
- `Pessoa13_PR.csv`
- `Domicilio01_PR.csv`

Saida atual:

- `data/ibge2010/cleaned/base_bairros_2010.csv`

Transformacoes estruturais:

- Filtragem dos dados para o municipio de Curitiba pelo codigo municipal.
- Extracao da relacao setor censitario -> bairro a partir de `Basico_PR.csv`.
- Criacao de `setores_bairro_curitiba` com:
  - `Cod_setor`
  - `Cod_bairro`
  - `Nome_do_bairro`
- Remocao de linhas sem `Cod_setor` ou `Cod_bairro`.
- Remocao de duplicidades nessa relacao.
- Uso de `Cod_setor` como chave para associar bases setoriais de renda, alfabetizacao e saneamento aos bairros.
- Agregacao final dos indicadores por `Cod_bairro` e `Nome_do_bairro`.

### Populacao

Transformacoes:

- Uso da variavel `V002` de `Basico_PR.csv` como populacao.
- Conversao numerica de `V002`.
- Soma por bairro.
- Criacao de `populacao_2010`.
- Tipagem como `Int64`.

### Renda das pessoas

Fonte: `PessoaRenda_PR.csv`.

Transformacoes:

- Merge com `setores_bairro_curitiba` por `Cod_setor`.
- Limpeza e conversao numerica das variaveis:
  - `V001`
  - `V002`
  - `V003`
  - `V006`
  - `V007`
  - `V008`
  - `V009`
  - `V010`
  - `V020`
- Soma das variaveis por bairro.
- Criacao dos indicadores:
  - `pessoas_10_anos_ou_mais` = `V020`
  - `pct_sem_rendimento` = `V010 / V020 * 100`
  - `pct_rendimento_ate_1_sm` = `(V001 + V002) / V020 * 100`
  - `pct_rendimento_ate_2_sm` = `(V001 + V002 + V003) / V020 * 100`
  - `pct_rendimento_acima_5_sm` = `(V006 + V007 + V008 + V009) / V020 * 100`

### Renda dos responsaveis pelo domicilio

Fonte: `ResponsavelRenda_PR.csv`.

Transformacoes:

- Merge com `setores_bairro_curitiba` por `Cod_setor`.
- Limpeza e conversao numerica das variaveis:
  - `V020`: total de responsaveis com ou sem rendimento
  - `V021`: total de responsaveis com rendimento positivo
  - `V022`: soma do rendimento nominal mensal dos responsaveis
- Soma por bairro.
- Criacao de:
  - `resp_domicilios_particulares` = `V020`
  - `rendimento_medio_responsavel` = `V022 / V021`, somente quando `V021 > 0`
  - `rendimento_medio_responsavel_sm` = `rendimento_medio_responsavel / 510`
- Merge desses indicadores com a base de renda das pessoas.

### Alfabetizacao

Fontes:

- `Pessoa01_PR.csv`: pessoas alfabetizadas por idade.
- `Pessoa13_PR.csv`: populacao por idade.

Transformacoes:

- Merge de ambas as bases com `setores_bairro_curitiba` por `Cod_setor`.
- Limpeza e conversao numerica das colunas de alfabetizacao e idade.
- Soma das colunas de idade para criar:
  - `alfabetizados_10mais`
  - `alfabetizados_15mais`
  - `pop_10mais`
  - `pop_15mais`
- Agregacao por bairro.
- Merge entre totais de alfabetizados e populacao por bairro.
- Criacao dos indicadores:
  - `pct_alfabetizacao_10mais` = `alfabetizados_10mais / pop_10mais * 100`
  - `pct_analfabetismo_10mais` = `100 - pct_alfabetizacao_10mais`
  - `pct_alfabetizacao_15mais` = `alfabetizados_15mais / pop_15mais * 100`
  - `analfabetos_15mais` = `pop_15mais - alfabetizados_15mais`
  - `pct_analfabetismo_15mais` = `100 - pct_alfabetizacao_15mais`

### Saneamento

Fonte: `Domicilio01_PR.csv`.

Transformacoes:

- Merge com `setores_bairro_curitiba` por `Cod_setor`.
- Limpeza e conversao numerica das variaveis:
  - `V002`
  - `V013`
  - `V014`
  - `V015`
  - `V019`
  - `V020`
  - `V021`
  - `V022`
  - `V023`
  - `V038`
  - `V039`
  - `V040`
  - `V041`
  - `V042`
- Soma por bairro.
- Criacao de:
  - `domicilios_particulares_permanentes` = `V002`
  - `sem_rede_geral_agua` = `V013 + V014 + V015`
  - `sem_banheiro_sanitario` = `V023`
  - `esgotamento_precario` = `V019 + V020 + V021 + V022 + V023`
  - `lixo_destino_inadequado` = `V038 + V039 + V040 + V041 + V042`
- Criacao de percentuais sobre `V002`:
  - `pct_sem_rede_geral_agua`
  - `pct_sem_banheiro_sanitario`
  - `pct_esgotamento_precario`
  - `pct_lixo_destino_inadequado`

### Unificacao final 2010

Transformacoes:

- Merge externo `1:1` entre:
  - populacao
  - renda
  - alfabetizacao
  - saneamento
- Limpeza textual de `Nome_do_bairro`.
- Remocao de `Cod_bairro`.
- Renomeacao de `Nome_do_bairro` para `ATENDIMENTO_BAIRRO_NOME`.
- Adicao do sufixo `_2010` a todas as colunas de indicadores.
- Padronizacao final dos nomes de bairro com `MAPA_BAIRRO` e ajustes especificos do IBGE 2010.
- Ajustes especificos do IBGE 2010:
  - `botiatuvinha` -> `butiatuvinha`
  - `cidade industrial de curitiba` -> `cidade industrial`
  - `alto da rua xv` -> `alto da xv`
  - `campo de santana` -> `campo do santana`
- Ordenacao por `ATENDIMENTO_BAIRRO_NOME`.

## IBGE Censo 2022

### Entrada e granularidade

Arquivos usados:

- `Agregados_por_bairros_basico_BR.csv`
- `Agregados_por_bairros_renda_responsavel_BR.csv`
- `Agregados_por_bairros_alfabetizacao_BR.csv`
- `Agregados_por_bairros_caracteristicas_domicilio1_BR.csv`
- `Agregados_por_bairros_caracteristicas_domicilio2_BR.csv`

Saida atual:

- `data/ibge2022/cleaned/base_bairros_2022.csv`

Transformacoes estruturais:

- Filtragem dos dados para Curitiba por `CD_MUN`.
- Extracao dos codigos de bairro de Curitiba a partir da base basica.
- Criacao da colecao `bairros_curitiba` com `CD_BAIRRO`.
- Filtro das bases de alfabetizacao, renda e domicilio usando `CD_BAIRRO`.
- Como os arquivos de 2022 ja estao agregados por bairro, nao ha etapa de relacionamento setor censitario -> bairro.

### Populacao

Transformacoes:

- Uso da variavel `v0001` da base basica como populacao.
- Conversao numerica.
- Soma por `CD_BAIRRO` e `NM_BAIRRO`.
- Criacao de `populacao_2022`.
- Tipagem como `Int64`.

### Renda dos responsaveis pelo domicilio

Fonte: `Agregados_por_bairros_renda_responsavel_BR.csv`.

Transformacoes:

- Renomeacao de variaveis:
  - `V06001` -> `resp_domicilios_particulares`
  - `V06002` -> `moradores_domicilios_particulares`
  - `V06004` -> `rendimento_medio_responsavel`
- Limpeza de `rendimento_medio_responsavel`:
  - remocao de espacos
  - remocao de ponto como separador de milhar
  - troca de virgula decimal por ponto
  - conversao numerica
- Criacao de `rendimento_medio_responsavel_sm` = `rendimento_medio_responsavel / 1212`.
- Remocao das variaveis de variancia:
  - `V06003`
  - `V06005`
- Selecao final das colunas de bairro e renda:
  - `CD_BAIRRO`
  - `NM_BAIRRO`
  - `resp_domicilios_particulares`
  - `moradores_domicilios_particulares`
  - `rendimento_medio_responsavel`
  - `rendimento_medio_responsavel_sm`
- Conversao numerica final das colunas de renda selecionadas.

### Alfabetizacao

Fonte: `Agregados_por_bairros_alfabetizacao_BR.csv`.

Transformacoes:

- Filtro para bairros de Curitiba por `CD_BAIRRO`.
- Criacao da lista `col_pop_15mais` com `V00644` a `V00656`.
- Criacao da lista `col_alfabetizados_15_mais` com `V00748` a `V00760`.
- Limpeza numerica das colunas selecionadas:
  - remocao de ponto como separador de milhar
  - troca de virgula por ponto
  - conversao numerica
- Soma por linha para criar:
  - `pop_15mais`
  - `alfabetizados_15mais`
- Criacao dos indicadores:
  - `pct_alfabetizacao_15mais` = `alfabetizados_15mais / pop_15mais * 100`
  - `analfabetos_15_anos_ou_mais` = `pop_15mais - alfabetizados_15mais`
  - `pct_analfabetismo_15mais` = `analfabetos_15_anos_ou_mais / pop_15mais * 100`
- Selecao final de:
  - `CD_BAIRRO`
  - `NM_BAIRRO`
  - `pop_15mais`
  - `alfabetizados_15mais`
  - `pct_alfabetizacao_15mais`
  - `pct_analfabetismo_15mais`

### Saneamento

Fontes:

- `Agregados_por_bairros_caracteristicas_domicilio1_BR.csv`
- `Agregados_por_bairros_caracteristicas_domicilio2_BR.csv`

Transformacoes:

- Filtro dos dois arquivos para bairros de Curitiba por `CD_BAIRRO`.
- Selecao das variaveis de `domicilio1`:
  - `V00001`
  - `V00002`
  - `V00052`
- Selecao das variaveis de `domicilio2`:
  - `V00238`
  - `V00312`
  - `V00313`
  - `V00314`
  - `V00316`
  - `V00464`
  - `V00399`
  - `V00400`
  - `V00401`
  - `V00402`
- Limpeza numerica das variaveis selecionadas.
- Merge `1:1` entre `domicilio1` e `domicilio2` por `CD_BAIRRO` e `NM_BAIRRO`.
- Soma por bairro.
- Criacao de:
  - `domicilios_particulares_permanentemente_ocupados_2022` = `V00001`
  - `sem_banheiro_sanitario_2022` = `V00238`
  - `esgotamento_precario_2022` = `V00312 + V00313 + V00314 + V00316`
  - `sem_rede_geral_agua_2022` = `V00464`
  - `lixo_destino_inadequado_2022` = `V00399 + V00400 + V00401 + V00402`
  - `domicilios_improvisados_estrutura_degradada_2022` = `V00002 + V00052`
- Criacao de percentuais usando `domicilios_particulares_permanentemente_ocupados_2022` como denominador:
  - `pct_sem_banheiro_sanitario_2022`
  - `pct_esgotamento_precario_2022`
  - `pct_sem_rede_geral_agua_2022`
  - `pct_lixo_destino_inadequado_2022`
  - `pct_domicilios_improvisados_estrutura_degradada_2022`

### Unificacao final 2022

Transformacoes:

- Merge externo `1:1` entre:
  - populacao
  - renda
  - alfabetizacao
  - saneamento
- Limpeza textual de `NM_BAIRRO`.
- Remocao de `CD_BAIRRO`.
- Renomeacao de `NM_BAIRRO` para `ATENDIMENTO_BAIRRO_NOME`.
- Adicao do sufixo `_2022` a todas as colunas de indicadores que ainda nao tinham o sufixo.
- Padronizacao final dos nomes de bairro com `MAPA_BAIRRO` e ajustes especificos do IBGE 2022.
- Ajustes especificos do IBGE 2022:
  - `botiatuvinha` -> `butiatuvinha`
  - `cidade industrial de curitiba` -> `cidade industrial`
- Ordenacao por `ATENDIMENTO_BAIRRO_NOME`.

## Observacoes para implementacao da silver

- A chave comum preparada pelas tres fontes e `ATENDIMENTO_BAIRRO_NOME`.
- A SIGESGUARDA permanece em granularidade de ocorrencia.
- Os censos sao agregados em granularidade de bairro.
- Os indicadores de 2010 devem manter sufixo `_2010`.
- Os indicadores de 2022 devem manter sufixo `_2022`.
- As regras de bairro e natureza devem ser centralizadas para evitar divergencia entre notebooks e pipeline.
- Recomenda-se validar unicidade de bairro nas bases censitarias antes dos merges `1:1`.
- Recomenda-se validar que cada ocorrencia da SIGESGUARDA tenha exatamente uma flag de categoria de natureza ativa.
- Recomenda-se revisar a implementacao do recorte de duplicidade da SIGESGUARDA antes de portar para a silver; a regra pretendida e comparar novembro de 2022 nas duas bases por `OCORRENCIA_CODIGO`.
