SELECT 
    ommlf.data,
    ommlf.log1p_lag_1,
    ommlf.log1p_lag_2,
    ommlf.log1p_lag_3,
    ommlf.log1p_lag_6,
    ommlf.log1p_lag_12,
    ommlf.log1p_media_3,
    ommlf.log1p_media_6,
    ommlf.log1p_media_12,
    ommlf.iqv,
    ommlf.log_pop,
    ommlf.tempo,
    ommlf.mes_sin_1,
    ommlf.mes_cos_1,
    ommlf.mes_sin_2,
    ommlf.mes_cos_2,
    ommlf.bairro,
    ommlf.categoria,
    ommlf.y
FROM gold.ocorrencias_mensais_ml_features AS ommlf
INNER JOIN gold.load_batches AS lb
    ON lb.batch_id = ommlf.batch_id 
WHERE 
    lb.is_current = true
        AND ommlf.categoria IN (
            'ACIDENTE_TRANSITO',
            'ATENDIMENTO_OPERACIONAL_ASSISTENCIAL',
            'CRIME_PATRIMONIAL',
            'CRIME_VIOLENTO',
            'CRIME_ORDEM_PUBLICA',
            'CRIME_DROGAS_SUBSTANCIAS'
        )
ORDER BY 
    ommlf.data,
    ommlf.bairro,
    ommlf.categoria