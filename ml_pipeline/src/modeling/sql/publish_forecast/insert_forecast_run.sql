INSERT INTO monthly_forecasts.forecast_runs (
    gold_batch_id,
    mlflow_model_name,
    model_alias,
    mlflow_run_id,
    forecast_month
)
VALUES (
    :gold_batch_id,
    :model_name,
    :model_alias,
    :mlflow_run_id,
    :forecast_month
)
RETURNING forecast_run_id
