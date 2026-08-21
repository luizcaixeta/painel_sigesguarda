INSERT INTO monthly_forecasts.monthly_forecasts (
    forecast_run_id,
    bairro,
    categoria,
    predicted_count
)
VALUES (
    :forecast_run_id,
    :bairro,
    :categoria,
    :predicted_count
)
