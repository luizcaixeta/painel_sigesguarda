SELECT
    data,
    bairro,
    categoria,
    y,
    tempo,
    iqv,
    log_pop
FROM gold.ocorrencias_mensais_ml_features
WHERE batch_id = :batch_id
ORDER BY
    data,
    bairro,
    categoria
