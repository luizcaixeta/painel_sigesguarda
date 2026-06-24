# Dicionario de Dados da Base Limpa SIGESGUARDA

A base de dados final do Sigesguarda abrange o período de 2009 até 02/04/2026. Ela foi obtida a partir do seguinte link:

https://dadosabertos.curitiba.pr.gov.br/conjuntodado/detalhe?chave=b16ead9d-835e-41e8-a4d7-dcc4f2b4b627

Nele, foram baixados os arquivos:

- `2024-02-01_sigesguarda_-_Base_de_Dados.csv`
- `2026-04-02_sigesguarda_-_Base_de_Dados.csv`

Para obter a base de dados final, é necessário inserir os arquivos `.csv` baixados no diretório `data/sigesguarda/raw` e exercutar os notebooks na seguinte ordem:

1. `01_configurando_base_de_dados.ipynb`
2. `02_limpeza_dos_dados.ipynb`

## Dicionario de dados

### 1. Local e atendimento

| Coluna                    | Tipo sugerido       | Descricao                                                                                                   |
|---------------------------|---------------------|-------------------------------------------------------------------------------------------------------------|
| `ATENDIMENTO_BAIRRO_NOME` | texto               | Bairro do atendimento após padronização e validação contra a lista oficial de bairros de Curitiba do IPPUC. |
| `FLAG_EQUIPAMENTO_URBANO` | inteiro binario     | Indica se a ocorrência envolve equipamento urbano.                                                          |
| `FLAG_FLAGRANTE`          | inteiro binario     | Indica se o atendimento ocorreu em situação de flagrante.                                                   |
| `LOGRADOURO_NOME`         | texto               | Nome do logradouro padronizado.                                                                             |
| `SECRETARIA_SIGLA`        | texto               | Sigla da secretaria associada ao atendimento.                                                               |
| `SERVICO_NOME`            | texto               | Nome do serviço responsável pelo atendimento.                                                               |
| `NUMERO_PROTOCOLO_156`    | texto identificador | Numero do protocolo `156`, quando existente.                                                                |

### 2. Naturezas originais da ocorrência

| Coluna                   | Tipo sugerido   |
|--------------------------|-----------------|
| `NATUREZA1_DEFESA_CIVIL` | inteiro binario |
| `NATUREZA1_DESCRICAO`    | texto           |
| `NATUREZA2_DEFESA_CIVIL` | inteiro binario |
| `NATUREZA2_DESCRICAO`    | texto           |
| `NATUREZA3_DEFESA_CIVIL` | inteiro binario |
| `NATUREZA3_DESCRICAO`    | texto           |
| `NATUREZA4_DEFESA_CIVIL` | inteiro binario |
| `NATUREZA4_DESCRICAO`    | texto           |
| `NATUREZA5_DEFESA_CIVIL` | inteiro binario |
| `NATUREZA5_DESCRICAO`    | texto           |

As features de descrição foram utilizadas para construção da features do bloco 4 desta documentação. 

### 3. Dimensoes temporais

| Coluna                   | Tipo sugerido      | Descricao                                          |
|--------------------------|--------------------|----------------------------------------------------|
| `ocorrencia_ANO`         | inteiro            | Ano da ocorrência.                                 |
| `ocorrencia_DIA_SEMANA`  | inteiro categorico | Dia da semana codificado numericamente.            |
| `ocorrencia_MES`         | inteiro            | Mes da ocorrência (`1` a `12`).                    |
| `ocorrencia_DIA`         | inteiro            | Dia do mes da ocorrência (`1` a `31`).             |
| `ocorrencia_HORA_HORA`   | inteiro            | Hora extraida de `ocorrência_HORA` (`0` a `23`).   |
| `ocorrencia_HORA_MINUTO` | inteiro            | Minuto extraido de `ocorrência_HORA` (`0` a `59`). |
| `MADRUGADA`              | inteiro binario    | Indicador de ocorrência entre `00:00` e `05:59`.   |
| `MANHA`                  | inteiro binario    | Indicador de ocorrência entre `06:00` e `11:59`.   |
| `TARDE`                  | inteiro binario    | Indicador de ocorrência entre `12:00` e `17:59`.   |
| `NOITE`                  | inteiro binario    | Indicador de ocorrência entre `18:00` e `23:59`.   |

As features `ocorrência_HORA_HORA`, `ocorrência_HORA_MINUTO`, `MADRUGADA`, `MANHA`, `TARDE` e `NOITE` foram construída a partir da coluna
de horário de registro da ocorrência, objetivando responder a perguntas como:

- Existe relação entre crimes violentos e o horário em que eles são comentidos? Por exemplo: crimes violentos ocorrem mais nos períodos noturnos?

Já as features `ocorrência_ANO`, `ocorrência_DIA_SEMANA` e `ocorrência_MES` foram criadas a partir da coluna de data do registro da ocorrência, 
objetivando padronizar a base antiga (dados de 2009 até 2022) com a base nova (dados de 2022 até 02/04/2026), facilitando uma futura análise 
temporal.

### 4. Features derivadas de classificacao tematica

Cada coluna abaixo vale `1` quando pelo menos uma das colunas `NATUREZA1_DESCRICAO` a `NATUREZA5_DESCRICAO` foi enquadrada na respectiva classe.

| Coluna | Tipo sugerido | Preenchimento | Descricao |
|--------|---------------|---------------|-----------|
| `CRIME_VIOLENTO`                   | inteiro binario | Indicador de ocorrência relacionada a crime violento.                                                         |
| `ATENDIMENTO_OPERACIONAL_ASSISTENCIAL`               | inteiro binario | Ocorrência relacionada a atendimento operacional, apoio, orientação, averiguação ou assistência.                                                     |
| `ACIDENTE_TRANSITO`                | inteiro binario | Indicador de ocorrência relacionada a acidente de trânsito.                                                   |
| `ACIDENTE_NATURAL`                 | inteiro binario | Indicador de ocorrência relacionada a evento natural ou ambiental.                                            |
| `CRIME_PATRIMONIAL`                | inteiro binario | Indicador de ocorrência relacionada a crime patrimonial.                                                      |
| `CRIME_ADMINISTRACAO_PUBLICA`      | inteiro binario | Indicador de ocorrência relacionada a crime contra a administração publica.                                   |
| `CRIME_HONRA_DISCRIMINACAO`        | inteiro binario | Indicador de ocorrência relacionada a honra, preconceito ou discriminação.                                    |
| `CRIME_CRIANCA_ADOLESCENTE`        | inteiro binario | Indicador de ocorrência relacionada a crianças e adolescentes.                                                |
| `CRIME_FRAUDE_DOCUMENTAL`          | inteiro binario | Indicador de ocorrência relacionada a fraude documental.                                                      |
| `CRIME_DROGAS_SUBSTANCIAS`         | inteiro binario | Indicador de ocorrência relacionada a drogas e outras substâncias lícitas ou ilícitas.                                            |
| `CRIME_ORDEM_PUBLICA`              | inteiro binario | Indicador de ocorrência relacionada a ordem pública.                                                          |
| `RISCO_ESTRUTURAL`                 | inteiro binario | Indicador de risco estrutural ou de seguranca fisica do local.                                                |
| `EXPLOSIVOS_E_PRODUTOS_PERIOGOSOS` | inteiro binario | Indicador de ocorrência relacionada a explosivos ou produtos perigosos.                                       |
| `PESSOAS_DESAPARECIDAS`            | inteiro binario | Indicador de ocorrência relacionada a pessoas desaparecidas.                                                  |
| `MATERIAIS_OBJETOS`                | inteiro binario | Indicador de ocorrência relacionada a materiais, objetos ou bens nao classificados nas categorias anteriores. |

1. As ocorrências que foram categorizadas como violentos são:

- abandono de incapaz;
- abuso de incapazes;
- agressao fisica verbal;
- ameaca;
- arrastao;
- atentado violento ao pudor;
- constrangimento ilegal;
- disparo de arma;
- estupro;
- extorsao;
- homicidio;
- importunacao ofensiva ao pudor;
- importunacao sexual;
- lesao corporal;
- maus tratos a pessoas;
- omissao de socorro;
- perseguicao stalking;
- posse sexual mediante fraude;
- resistencia;
- rixa;
- roubo;
- sequestro e carcere privado;
- tentativa de homicidio;
- vias de fato;
- violacao de medida protetiva lei maria da penha;
- violencia arbitraria;
- roubo furto extravio recuperacao apreensao de armas de fogo.

2. Ocorrências categorizadas como atendimento operacional e assistencial:

- aifu;
- alarmes;
- antecedentes criminais verificacao;
- apoio;
- atitude suspeita;
- averiguacao;
- averiguacao cosedi;
- averiguacao defesa civil;
- denuncia improcedente;
- encaminhamento;
- envenenamento;
- escolta;
- evento;
- fiscalizacoes e orientacoes;
- fundada suspeita abordagem;
- liberacao de pessoa presa apreendida por recusa no recebimento pela dp;
- notificacao;
- obito;
- obito defesa civil;
- orgaos acionados;
- orientacao;
- paciente usuario alterado;
- patrulha maria da penha;
- protecao ao patrimonio;
- ronda;
- saturacao;
- suicidio.


3. Ocorrências categorizadas como acidente de trânsito:

- acidente de transito;
- acidente viatura;
- transito;
- queda de aeronave;
- veiculo.

4. Ocorrências categorizadas como causas naturais:

- abalo sismico;
- alagamento;
- animais;
- ataque cao feroz;
- ataque de insetos;
- bueiro aberto sem tampa;
- bueiro entupido;
- deslizamento de terra;
- enxurrada;
- erosao;
- inundacao enchente;
- pragas animais;
- poda de arvore;
- poluicao visual ambiental;
- queda de arvore;
- queda de galho;
- risco de queda de arvore;
- risco de queda de galho;
- rompimento de barragem.

5. Ocorrências relacionadas a crimes patrimonias:

- apropriacao indebita;
- calote;
- dano;
- estelionato;
- furto;
- invasao;
- receptacao;
- roubo furto extravio recuperacao apreensao de armas de fogo.

6. Ocorrências relacionadas a administração pública

- abandono de funcao;
- contrabando ou descaminho;
- concussao;
- corrupcao ativa;
- desacato;
- desobediencia;
- fingir se funcionario publico;
- obstrucao da atividade policial;
- peculato;
- prevaricacao;
- recusar se identificar ao policial;
- tentativa de suborno;
- usar de uniforme ou distintivo de funcao publica que nao exerce.

7. Ocorrências relacionadas a crimes que ferem a honra ou discriminação:

- calunia;
- difamacao;
- discriminacao;
- homofobia;
- injuria;
- racismo.

8. Ocorrências relacionadas a crimes contra a criança ou adolescente:

- aliciamento de menor;
- corrupcao de menores;
- exploracao de menores;
- fornecimento de bebida alcoolica a menores;
- seducao;
- venda proibida de produtos especificos a menores.

9. Ocorrências relacionadas a fraude documental:

- extravio sonegacao ou inutilizacao de livro ou doc;
- falsidade ideologica falsa identidade;
- falsificacao de documento publico;
- moeda falsa;
- uso indevido do cartao transporte;
- uso indevido do telefone publico.

10. Ocorrências relacionadas a substâncias lícitas e ilícitas:

- embriaguez;
- substancia ilicita;
- substancia licita.

11. Ocorrências relacionadas a ordem pública:

- apologia de crime ou criminoso;
- atos obscenos libidinosos;
- crime ambiental;
- favorecimento da prostituicao;
- impedimento ou perturbacao de cerimonia funeraria;
- incitacao ao crime;
- charlatanismo;
- jogo de azar;
- maus tratos a animais;
- mendigar por ociosidade ou cupidez;
- panfletagem pornografica;
- pesca em local proibido;
- perturbacao do sossego;
- porte ilegal;
- prostituicao;
- quadrilha ou bando;
- rufianismo;
- trote telefonico;
- vadiagem;
- vilipendio a cadaver;
- violacao de sepultura tumulo;
- banho em local improprio.

12. Ocorrências relacionadas a risco estrutural:

- afundamento de piso;
- desabamento;
- desabamento de telhado cobertura;
- infiltracao;
- queda de fios de energia;
- queda de muro;
- queda de poste;
- queda de revestimento de fachadas;
- quedas de objetos ou partes de construcoes;
- rachadura em edificacao;
- risco de acidente a vida;
- risco de acidente a vida defesa civil;
- risco de desabamento desmoronamento;
- risco de queda de fios de energia;
- risco de queda de poste;
- situacao de risco.

13. Ocorrências relacionadas a explosivos e produtos perigosos:

- denuncia de bomba;
- explosao;
- incendio;
- incendio explosao em edificacao;
- manipulacao de explosivo;
- porte de artefato explosivo;
- queima a ceu aberto;
- risco de explosao;
- vazamento ou derramamento de produto perigoso ou infectante.

14. Ocorrências relacionadas a pessoas desparecidas:

- afogamento;
- crianca perdida desaparecida;
- desaparecimento.

15. Ocorrências relacionadas a materiais e objetivos:

- achado;
- apreensao de materiais;
- devolucao de coisa achada;
- extravio de documento;
- extravio de equipamento;
- material abandonado;
- recolhimento de materiais.

## Campos removidos ou substituidos no conjunto final

As colunas abaixo aparecem em versoes anteriores da base ou na materia-prima, mas nao fazem parte do arquivo final documentado aqui:

- `ATENDIMENTO_ANO`
- `EQUIPAMENTO_URBANO_NOME`
- `SUBCATEGORIA1_DESCRICAO`
- `SUBCATEGORIA2_DESCRICAO`
- `SUBCATEGORIA3_DESCRICAO`
- `SUBCATEGORIA4_DESCRICAO`
- `SUBCATEGORIA5_DESCRICAO`
- `ocorrencia_CODIGO`
- `ocorrencia_DATA`
- `ocorrencia_HORA`
- `OPERACAO_DESCRICAO`
- `ORIGEM_CHAMADO_DESCRICAO`
- `REGIONAL_FATO_NOME`
- `SECRETARIA_NOME`
- `SITUACAO_EQUIPE_DESCRICAO`