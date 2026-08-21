import os

import mlflow
import numpy as np
from sqlalchemy import create_engine

from modeling.config import (
    ALIAS_NAME, 
    FEATURES, 
    MLFLOW_MODEL_NAME
)
from modeling.data import (
    SQL_DIR, 
    db_url, 
    load_sql_into_dataframe, 
    read_sql
)
from modeling.future_features import build_future_features

CURRENT_BATCH_QUERY = read_sql(SQL_DIR, 'publish_forecast', 'current_batch.sql')
HISTORY_QUERY = read_sql(SQL_DIR, 'publish_forecast', 'history.sql')
INSERT_FORECAST_RUN = read_sql(SQL_DIR, 'publish_forecast', 'insert_forecast_run.sql',)
INSERT_FORECASTS = read_sql(SQL_DIR, 'publish_forecast', 'insert_forecasts.sql',)

def main() -> None:
    mlflow.set_tracking_uri(os.environ['MLFLOW_TRACKING_URI'])

    model_version = mlflow.MlflowClient().get_model_version_by_alias(
        MLFLOW_MODEL_NAME,
        ALIAS_NAME,
    )
    model = mlflow.pyfunc.load_model(
        f'models:/{MLFLOW_MODEL_NAME}@{ALIAS_NAME}'
    )

    engine = create_engine(db_url)

    with engine.connect() as connection:
        batch = connection.execute(CURRENT_BATCH_QUERY).mappings().one()

    history = load_sql_into_dataframe(
        HISTORY_QUERY.bindparams(batch_id=batch['batch_id'])
    )
    future = build_future_features(history)
    future['predicted_count'] = np.maximum(
        0,
        np.floor(model.predict(future[FEATURES]) + 0.5),
    ).astype(int)

    with engine.begin() as connection:
        forecast_run_id = connection.execute(
            INSERT_FORECAST_RUN,
            {
                'gold_batch_id': batch['batch_id'],
                'model_name': MLFLOW_MODEL_NAME,
                'model_alias': ALIAS_NAME,
                'mlflow_run_id': model_version.run_id,
                'forecast_month': future['data'].iat[0],
            },
        ).scalar_one()

        forecast_rows: list[dict[str, object]] = [
            {
                'forecast_run_id': forecast_run_id,
                'bairro': bairro,
                'categoria': categoria,
                'predicted_count': int(predicted_count),
            }
            for bairro, categoria, predicted_count in future[
                ['bairro', 'categoria', 'predicted_count']
            ].itertuples(index=False, name=None)
        ]

        connection.execute(
            INSERT_FORECASTS,
            forecast_rows,
        )

    print(
        f"Forecast {future['data'].iat[0]:%Y-%m} published: "
        f'{len(future)} series, model {MLFLOW_MODEL_NAME} '
    )

if __name__ == "__main__":
    main()
