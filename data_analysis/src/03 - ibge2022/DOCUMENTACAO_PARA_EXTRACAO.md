# Objetivo 

Os dados extraídos serão utilizados para investigar possíveis relações entre fatores socioeconômicos e as ocorrências registradas pela SIGESGUARDA, permitindo análises como:

- relação entre renda e crimes violentos;
- relação entre renda e crimes patrimoniais;
- relação entre alfabetização e ocorrências registradas;
- comparação entre bairros com diferentes níveis de vulnerabilidade socioeconômica;
- cálculo de taxas de ocorrências por população residente.

**Observação importante:**: 

Os dados do censo de 2022 foram disponibilizados pelo IBGE já agregados em nível de bairro, não sendo necessário relacionar setores censitários aos bairros de Curitiba. Assim, as informações socioeconômicas foram extraídas diretamente das tabelas de agregados por bairroe  filtradas para o município de Curitiba por meio do código municipal e dos códigos de bairro. 

---

# Fontes utilizadas

AS informações utilizadas nessa etapa do trabalho foram extraídas da documentação oficial do IBGE referentes as variáveis do universo do Censo Demográfico de 2022.

Fontes:

1. Documentação oficial: 

https://biblioteca.ibge.gov.br/visualizacao/livros/liv102136.pdf

Dicionários de dados para o censo de 2022:

https://www.ibge.gov.br/estatisticas/downloads-estatisticas.html

3. Para validação dos resultados, foi utilizada a referência:

https://cidades.ibge.gov.br/brasil/pr/curitiba/panorama

https://app.powerbi.com/view?r=eyJrIjoiZmFjMjQwMDItMDIyMC00YWQyLWJiZDYtMmI4ZDJlN2FiNTcwIiwidCI6IjU3NWNkYTA5LTg5OWYtNDJmMy04NGM1LWRmOGQ2YzZmMzM5YSJ9

---

# Estrutura dos dados do censo demográfico 2022

Os dados do censo dedmográfico de 2022 utilizados neste projeto estão organizados em arquivos temáticos já agregados em nível de bairro. DIferentemente do Censo 2010, não foi necessário relacionar setores censitários aos bairros, pois o IBGE disponibiliza os arquivos específicos de agregados por bairro.

Os arquivos utilizados foram:

```
dados_ibge_2022/
├── Agregados_por_bairros_basico_BR.zip
├── Agregados_por_bairros_alfabetizacao_BR.zip
├── Agregados_por_bairros_rendimento_responsavel_BR.zip
└── dicionario_de_dados_renda_responsavel.xlsx
```

E podem ser obtidos em:


https://www.ibge.gov.br/estatisticas/downloads-estatisticas.html

---

## Básico

Contém os códigos e nomes da subdvisões geográficas, além das informações básicas da população por bairro.

Esse arquivo foi utilizado principalmente para identificar:

- município;
- bairro;
- população total do bairro.

A variável correspondente a população total do bairro é `V0001`. Esse arquivo também foi usado como base para filtrar os bairros pertencentes a Curitiba, por meio do código municipal:

`CD_MUN = 4106902`

Esse código municipal foi obtido em:

https://www.ibge.gov.br/cidades-e-estados/pr/curitiba.html

A partir dele, foram identificados os códigos dos bairros de Curitiba (`CD_BAIRRO`), posteriormente utilizados para filtrar os arquivos de alfabetização e renda.

## Alfabetização

Contém informações sobre alfabetização da população residente, organizadas por grupos de idade e outras aberturas populacionais.

Nesse projeto, os dados de alfabetização foram extraídos em nível de bairro. Portanto, não foi necessário associar setores censitários aos bairros, como ocorreu no Censo 2010.

A metodologia utilizada seguiu as seguintes etapas:

1. identificar os bairros de Curitiba no arquivo básico (feito na etapa anterior);
2. usar os códigos de bairro para filtra o arquivo de alfabetização;
3. obter a população de 15 anos ou mais;
4. obter a quantidade de pessoas alfabetizadas de 15 anos ou mais;
5. calcular a taxa percentual de alfabetização por bairro.

Para o cálculo da taxa de alfabetização de 15 anos ou mais, foram utilizadas variáveis refentes à população total da faixa etária e à população alfabetizada da mesma faixa etária, filtrando por bairros.

As variáveis utilizadas foram:

- `V00644` a `V00656` = pessoas de 15 anos ou mais;
- `V00748` a `V00760` = pessoas alfabetizadas de 15 anos ou mais.

Nesse projeo, a alfabetização foi calculada apenas para a população de 15 anos ou mais. A variável de alfabetização para 10 anos ou mais não foi utilizada, pois o arquivo disponível não permitiu identificar essa faixa etária.

## Renda

Contém informações sobre o rendimento nominal mensal das pessoas responsáveis pelos domicílios particulares ocupados.

No censo de 2022, o arquivo utilizado de rendimento do responsável não apresenta faixas de renda em salários mínimos, como "até 1 salário mínimo", "até 2 salários mínimos" ou "mais de 5 salários mínimos". Em vez disso, ele apresenta informações agregadas sobre responsáveis, moradores e rendimento médio.

As principais variáveis disponíveis nesse arquivo são:

- `V06001` = pessoas responsáveis por domicílios particulares ocupados;
- `V06002` = moradores em domicílios particulares ocupados;
- `V06003` = variância do número de moradores;
- `V06004` = rendimento nominal médio mensal das pessoas responsáveis com rendimento;
- `V06005` = variância do rendimento nominal mensal.

Dessa forma, a metodologia utilizada foi:

1. identificar os bairros de Curitiba a partir do arquivo básico (feito na primeira etapa);
2. filtrar o arquivo de renda usando os códigos de bairro;
3. extrair o número de responsáveis por domicílios particulares ocupados;
4. extrair o número de moradores em domicílios particulares ocupados;
5. extrair o rendimento médio mensal dos responsáveis;
6. converter o rendimento médio para salários mínimos de 2022.

A conversão para salários mínimos foi feita com base no salário mínimo de 2022, de R$ 1.212,00:

$$
\text{Rendimento médio em salários mínimos} = \frac{\text{Rendimento médio do responsável}}{1212}
$$

Assim, os indicadores de renda utilizados foram:

- número de responsáveis por domicílios particulares ocupados;
- número de moradores em domicílios particulares ocupados;
- rendimento médio mensal do responsável;
- rendimento médio mensal do responsável em salários mínimos.

As taxas por faixa de salário não foram calculadas pois o arquivo disponível não contém a contagem de responsáveis por faixas de rendimento.

## Saneamento básico

Contém informações sobre características dos domicílios particulares permanentemente ocupados, especialmente quanto à existência de banheiro ou sanitário, esgotamento sanitário, abastecimento de água, destino do lixo e condições estruturais do domicílio.

Nesse projeto, os dados de saneamento básico foram extraídos em nível sde bairro. Portanto, não foi necessário associar setores censitários aos bairros, como ocorreu no Censo 2022.

As variáveis utilizadas para construir os indicadores foram:

- `V00001`: domicílios particulares permanentes ocupados;
- `V00002`: domicílios particulares improvisados Ocupados;
- `V00052`: domicílios particulares permanentes ocupados, tipo de espécie é estrutura residencial permanente degradada ou inacabada;
- `V00238`: domicílios particulares permanentes ocupados, não tinham banheiro nem sanitário;
- `V00312`: domicílios particulares permanentes ocupados, destinação do esgoto do banheiro ou sanitário ou buraco para dejeções é fossa rudimentar ou buraco;
- `V00313`: domicílios particulares permanentes ocupados, destinação do esgoto do banheiro ou sanitário ou buraco para dejeções é vala;
- `V00314`: domicílios particulares permanentes ocupados, destinação do esgoto do banheiro ou sanitário ou buraco para dejeções é rio, lago, córrego ou mar;
- `V00315`: domicílios particulares permanentes ocupados, destinação do esgoto do banheiro ou sanitário ou buraco para dejeções é outra forma
- `V00316`: domicílios particulares permanentes ocupados, destinação do esgoto inexistente, pois não tinham banheiro nem sanitário;
- `V00399`: domicílios particulares permanentes ocupados, lixo queimado na propriedade;
- `V00400`: domicílios particulares permanentes ocupados, lixo enterrado na propriedade;
- `V00401`: domicílios particulares permanentes ocupados, lixo jogado em terreno baldio, encosta ou área pública;
- `V00402`: domicílios particulares permanentes ocupados, outro destino do lixo;
- `V00464`: domicílios particulares permanentes ocupados, domicílio não possui ligação à rede geral de distribuição de água.

Os indicadores calculados foram:

- domicílios sem banheiro ou sanitário;
- percentual de domicílios sem banheiro ou sanitário;
- domicílios com esgotamento sanitário precário;
- percentual de domicílios com esgotamento sanitário precário;
- domicílios sem abastecimento de água pela rede geral;
- percentual de domicílios sem abastecimento de água pela rede geral;
- domicílios com destino inadequado do lixo;
- percentual de domicílios com destino inadequado do lixo;
- domicílios improvisados ou em estrutura degradada;
- percentual de domicílios improvisados ou em estrutura degradada.

Para o cálculo dos percentuais, foi utilizada a fórmula:

$$
  \text{Percentual do indicador} = \frac{\text{Quantidade de domicílios no indicador}}{\text{Domicílios particulares permanentemente ocupados}} \times 100
$$

