SELECT
    batch_id,
    data_through
FROM gold.load_batches
WHERE
    dataset = 'ml_features'
    AND is_current = true
