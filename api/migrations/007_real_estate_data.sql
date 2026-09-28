-- Write your migrate up statements here

/*
Queremos obter os dados imobiliários, para isso nós precisamos:

- bairros: precisamos puxar os bairros da tabela padrão do IPPUC
- valor: valor do imóvel
- tipo de contrato: dois enums: aluguel e venda
- tipo de imóvel: apartamento, casa, studio ou kitnet
- quantidade de quartos: número inteiro
- quantidade de banheiros: número inteiro
- tamanho do imóvel: número decimal (em metros quadrados)
- quantidade de vagas de garagem: número inteiro
- id do imóvel: chave primária do imóvel
- imobiliária: nome da imobiliária que está vendendo/alugando o imóvel
- data em que foi feito o scrape: data em que os dados do imóvel foram coletados

O objetivo de obter o id do imóvel e o nome da imobiliária é evitar repetição de dados
*/

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS gold.real_estate_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bairro_id TEXT NOT NULL REFERENCES gold.dim_bairros(bairro_id),
    valor_aluguel NUMERIC CHECK (valor_aluguel >= 0),
    valor_condominio NUMERIC CHECK (valor_condominio >= 0),
    valor_venda NUMERIC CHECK (valor_venda >= 0),
    tipo_contrato TEXT NOT NULL CHECK 
        (
            tipo_contrato IN (
                'aluguel', 
                'venda'
            )
        ),
    tipo_imovel TEXT CHECK 
        (
            tipo_imovel IN (
                'apartamento', 
                'casa', 
                'studio', 
                'kitnet'
            )
        ),
    quantidade_quartos INTEGER CHECK (quantidade_quartos >= 0),
    quantidade_banheiros INTEGER CHECK (quantidade_banheiros >= 0),
    tamanho_imovel NUMERIC CHECK (tamanho_imovel >= 0),
    quantidade_vagas_garagem INTEGER CHECK (quantidade_vagas_garagem >= 0),
    url_anuncio TEXT NOT NULL,
    id_imovel TEXT NOT NULL,
    nome_imobiliaria TEXT NOT NULL,
    data_scrape DATE NOT NULL DEFAULT CURRENT_DATE,
    collected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (nome_imobiliaria, id_imovel, tipo_contrato, data_scrape)
);

COMMIT;

---- create above / drop below ----

BEGIN;

DROP TABLE IF EXISTS gold.real_estate_data;

COMMIT;

-- Write your migrate down statements here. If this migration is irreversible
-- Then delete the separator line above.
