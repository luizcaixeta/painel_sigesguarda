## 1. Baixar os dados necessários 

Os dados da SIGESGUARDA devem ser baixados manualmente no portal de dados abertos da Prefeitura de Curitiba: 

https://dadosabertos.curitiba.pr.gov.br/conjuntodado/detalhe?chave=b16ead9d-835e-41e8-a4d7-dcc4f2b4b627

Nele, baixe os arquivos:

- `2024-02-01_sigesguarda_-_Base_de_Dados.csv`
- `2026-04-02_sigesguarda_-_Base_de_Dados.csv`

e coloque os arquivos `.csv` no diretório:

`data/sigesguarda/raw`

Os dados do censo do IBGE 2022 também devem ser baixados manualmente no portal de downloads do IBGE:

https://www.ibge.gov.br/estatisticas/downloads-estatisticas.html

Os arquivos esperados são os agregados por bairro, principalmente:

- `Agregados_por_bairro_basico_BR`
- `Agregados_por_bairros_alfabetizacao_BR`
- `Agregados_por_bairros_renda_responsavel_BR`

Eles devem ser salvos em:

`data/ibge2022/raw`

## 2. Executar os notebooks na ordem correta 

Execute os notebooks de cima para baixo, nesta ordem:

1. `src/01 - sigesguarda/01_configurando_base_de_dados.ipynb`
   
Esse notebook lê os arquivos brutos da SIGESGUARDA em:

`data/sigesguarda/raw`

E gera:

`data/sigesguarda/base_de_dados/base_unificada.csv`

2. `src/01 - sigesguarda/02_limpeza_dos_dados.ipynb`

Esse notebook limpa e padroniza a base da SIGESGUARDA.

Ele gera:

`data/sigesguarda/cleaned/base_unificada.csv`

3. `src/02 - ibge2010/01_configurando_base_de_dados.ipynb`

Esse notebook prepara os dados do censo do IBGE de 2010 por bairro.

Ele gera:

`data/ibge2010/cleaned/base_bairros_2010.csv`

4. `src/03 - ibge2022/01_configurando_base_de_dados.ipynb`

Esse notebook prepara os dados do censo do IBGE 2022 por bairro.

Ele gera:

`data/ibge2022/cleaned/base_bairros_2022.csv`

5. `src/04 - analise_de_dados/01_extrapolacao_linear.ipynb`

Esse notebook junta a base limpa da SIGESGUARDA com os indicadores do IBGE 2010 e 2022.

Ele gera a base final: 

`data/base_de_dados_final/base_sigesguarda_socioeconomica.csv`

6. `src/04 - analise_de_dados/02_analise_de_dados.ipynb`

Esse notebook utiliza a base final para gerar as análises e gráficos.

## 3. Para acessar diretamente a base de dados final

Caso não queira rodar todos os notebooks de preparação e queira utilizar somente a base final já preparada, ela está disponível para download em:

https://drive.google.com/drive/folders/1Z6DoN5u0nQy3vcoayqJlUuNLqmdq2bw_?usp=sharing


O arquivo final é:

`base_sigesguarda_socioeconomica.csv`

Essa base corresponde ao resultado da integração entre os dados da SIGESGUARDA e os indicadores socioeconomicos dos censos do IBGE.