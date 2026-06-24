# Objetivo

Os dados extraídos serão utilizados para investigar possíveis relações entre fatores socioeconômicos e as ocorrências registradas pela SIGESGUARDA, permitindo análises como:

- relação entre renda e crimes violentos;
- relação entre renda e crimes patrimoniais;
- relação entre alfabetização e ocorrências registradas;
- comparação entre bairros com diferentes níveis de vulnerabilidade socioeconômica;
- cálculo de taxas de ocorrências por população residente.

Como os dados do Censo 2010 são disponibilizados originalmente em nível de setor censitário, foi necessário relacionar os setores aos bairros de Curitiba e, posteriormente, agregar as informações socioeconômicas em nível de bairro.

---

# Fontes utilizadas

As informações utilizadas nessa etapa do trabalho foram extraídas da documentação oficial do IBGE referentes as variáveis do universo do Censo Demográfico de 2010 por setores censitários.

Fontes: 

1. Documentação oficial: para compreensão da base de dados foi utilizado o conteúdo da página 34-36, 45-46, 79-81, 140-143, 163-171.

https://www.cidadessustentaveis.org.br/arquivos/SIG/documentacao-sig/IBGE_BR-Setores-Censitarios_Censo%202010_Variaveis-universo.pdf 
  
2. Além da documentação oficial, a seguinte monografia serviu de apoio para compreensão de execução prática:

http://www.repositorio.poli.ufrj.br/monografias/monopoli10026310.pdf

3. Para validação dos resultados (ainda não concluída), está sendo utilizada a referência:

- https://www.coreconpr.gov.br/wp-content/uploads/2016/07/bairros.pdf

Ainda, foi utilizado como tutorial breve:

1. https://ipeagit.github.io/censobr_oficina_abep_2024/5_agregados_setores.html

---

# Estrutura dos dados do censo demográfico 2010

Os dados do censo demográfico de 2010 foram obtidos via FTP do IBGE no diretório:

```
/Censos/Censo_Demografico_2010/Resultados_do_Universo/Agregados_por_Setores
```

os dados são disponibilizados separadamente para cada Unidade da Federação (UF). Neste projeto, serão utilizado os arquivos referentes ao estado do Paraná, filtrando para o município de Curitiba.

---

# Organização dos arquivos

Os dados do censo demográfico de 2010 estão organizados em grupos temáticos. Cada grupo contém informações específicas sobre população, domicílios e características socioeconômicas. Os grupos de arquivos utilizados foram:

## Básico

Contém os códigos e nomes das subdivisões geográficas, além das informações básicas do cadastro territorial.

Esse grupo foi fundamental para relacionar:

- setor censitário;
- município;
- bairro.

## Alfabetização

Contém informações sobre alfabetização da população residente, organizadas por sexo e idade. Esses dados foram utilizados para calcular indicadores de alfabetização e analfabetismo por bairro.

Para isso, os dados de alfabetização foram extraídos em nível de setor censitário e posteriormente relacionados aos bairros de Curitiba por meio do arquivo `Basico_PR.csv`.

Como o arquivo de alfabetização contém apenas a quantidade de pessoas alfabetizadas, s
também foi utilizado os dados de população por faixa etária para calcular as taxas percentuais.

A metodologia utilizada seguiu as seguintes etapas:

1. identificar os setores censitários pertencentes a Curitiba (feito na etapa anterior);
2. relacionar cada setor censitário ao respectivo bairro;
3. obter a quantidade de pessoas alfabetizadas por setor censitário;
4. obter a população total da mesma faixa etária;
5. agregar os dados por bairro;
6. calcular os percentuais de alfabetização e analfabetismo.

Para a taxa de analfabetismo, foi utilizado:

$$
    \text{Analfabetismo} = 100 - \text{Alfabetização}
$$

Nesse projeto as taxas foram calculadas para a população de 15 anos ou mais.

## Renda 

Contém informações sobre rendimento nominal mensal da população, domicílios e responsáveis pelos domicílios. Esses dados foram utilizados para calcular indicadores de renda e vulnerabilidade econômica por bairro.

Os dados de renda foram extraídos em nível de setor censitário e associados aos bairros por meio do arquivo `Basico_PR.csv`, seguindo a metodologia anterior. 

A metodologia utilizada seguiu as seguintes etapas:

1. identificar os setores censitários pertencentes a Curitiba (feito na primeira etapa);
2. relacionar cada setor censitário ao respectivo bairro;
3. extrair as variáveis de renda por setor censitário;
4. agregar os dados por bairro;
5. calcular indicadores percentuais de renda.

Os percentuais calculados foram:

- percentual de pessoas sem rendimento;
- percentual de pessoas com rendimento de até 1 salário mínimo;
- percentual de pessoas com rendimento de até 2 salários mínimos;
- percentual de pessoas com rendimento acima de 5 salários mínimos.

Todas as taxas foram calculadas em relação a população do bairro.

### PessoaRenda

Além do arquivo `PessoaRenda_PR.csv`, utilizado para calcular percentuais de renda da população de 10 anos ou mais, também foi utilizado o arquivo `ReponsavelRenda_PR.csv` para calcular indicadores de renda das pessoas responsáveis pela moradia. Isso foi necessário para ajustar as métricas calculadas às métricas do censo de 2022, uma vez que no censo de 2022 estão disponíveis somente dados sobre a renda das pessoas responsáveis pela moradia.

Nesse arquivo, as variáveis `V020`, `V021` e `V022` foram usadas para obter o número de responsáveis e o rendimento médio mensal dos responsáveis do bairro:

- `V020`: total de responsáveis com ou sem rendimento por bairro;
- `V021`: total de responsáveis com rendimentos positivo;
- `V022`: soma do rendimento nominal mensal dos responsáveis.

## Saneamento básico 

Contém informações sobre características dos domicílios particulares permanentes, especialmente quanto ao abastecimento de água, esgotamento sanitário, existência de banheiro ou sanitário e destino do lixo. Esses dados foram utilizados para calcular indicadores de saneamento básico por bairro. 

Para isso, os dados de saneamento foram extraídos em nível de setor censitário a partir do arquivo `Domicilio01_PR.csv` e posteriormente relacionados aos bairros de Curitiba por meio do arquivo `Basico_PR.csv`.

Como o arquivo de domicílios contém a quantidade de domicílios por tipo de infraestrutura, foi utilizado o total de domicílios particulares permanentes como denominador para calcular as taxas percentuais.

A metodologia utilizada seguiu as seguintes etapas:

1. identificar os setores censitários pertencentes a Curitiba;
2. relacionar cada setor censitário ao respectivo bairro;
3. extrair as variáveis de saneamento básico por setor censitário;
4. agregar os dados por bairro;
5. calcular os indicadores absolutos de sanemaneto;
6. calcular os percentuais em relação ao total de domicílios particulares permanentes.

Os indicadores calculados foram:

- domicílios sem abastecimento de água pela rede geral;
- domicílios sem banheiro de uso exclusivo dos moradores e sem sanitário;
- domicílios com esgotamento sanitário precário;
- domicílios com destino inadequado do lixo.

As variáveis utilizadas foram extraídas do arquivo Domicilio01_PR.csv:

- `V002`: domicílios particulares permanentes;
- `V013`: domicílios com abastecimento de água de poço ou nascente na propriedade;
- `V014`: domicílios com abastecimento de água da chuva armazenada em cisterna;
- `V015`: domicílios com outra forma de abastecimento de água;
- `V019`: domicílios com esgotamento sanitário via fossa rudimentar;
- `V020`: domicílios com esgotamento sanitário via vala;
- `V021`: domicílios com esgotamento sanitário via rio, lago ou mar;
- `V022`: domicílios com esgotamento sanitário via outro escoadouro;
- `V023`: domicílios sem banheiro de uso exclusivo dos moradores e nem sanitário;
- `V038`: domicílios com lixo queimado na propriedade;
- `V039`: domicílios com lixo enterrado na propriedade;
- `V040`: domicílios com lixo jogado em terreno baldio ou logradouro;
- `V041`: domicílios com lixo jogado em rio, lago ou mar;
- `V042`: domicílios com outro destino do lixo.

Para os percentuais, foi utilizado:

$$
  \text{Percentual do indicador} = \frac{\text{Quantidade de domicílios no indicador}}{\text{Domicílios particulares permanentes}} \times 100
$$