import mlflow
from mlflow.sklearn import log_model as log_sklearn_model
import numpy as np
from mlflow.models import infer_signature
from sklearn.compose import ColumnTransformer
from sklearn.metrics import make_scorer
from sklearn.model_selection import cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBRegressor

from modeling.config import (
    FEATURES,
    FEATURES_CATEGORICAS,
    FEATURES_NUMERICAS,
    TARGET,
    params,
)
from modeling.data import db_url, load_gold_dataframe
from modeling.split import make_time_series_split

def total_error(y_true, y_pred) -> float:
    return float(np.sum(y_pred) - np.sum(y_true))

def relative_bias(y_true, y_pred) -> float:
    actual_total = float(np.sum(y_true))

    if actual_total == 0:
        return 0.0

    return total_error(y_true, y_pred) / actual_total

def main() -> Pipeline:
    # 1. Dados
    df_ml = load_gold_dataframe(db_url)

    X = df_ml[FEATURES]
    y = df_ml[TARGET]

    # 2. Pre-processamento
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), FEATURES_NUMERICAS),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                FEATURES_CATEGORICAS,
            ),
        ]
    )

    # 3. Modelo
    model = XGBRegressor(**params)

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", model),
        ]
    )

    # 4. Validacao temporal: primeiro fold em 2017-01, depois mes a mes
    splitter = make_time_series_split(df_ml)

    scoring = {
        "error": make_scorer(total_error),
        "mae": "neg_mean_absolute_error",
        "bias": make_scorer(relative_bias),
        "poisson_deviance": "neg_mean_poisson_deviance",
    }

    mlflow.set_experiment("SIGESGUARDA training")

    with mlflow.start_run():
        mlflow.log_params(params)

        cv_results = cross_validate(
            estimator=pipeline,
            X=X,
            y=y,
            cv=splitter,
            scoring=scoring,
            return_train_score=False,
            n_jobs=1,
        )

        error_folds = cv_results["test_error"]
        mae_folds = -cv_results["test_mae"]
        bias_folds = cv_results["test_bias"]
        poisson_folds = -cv_results["test_poisson_deviance"]

        # Step 1 = 2017-01, step 2 = 2017-02, etc.
        for step, (error, mae, bias, poisson) in enumerate(
            zip(error_folds, mae_folds, bias_folds, poisson_folds),
            start=1,
        ):
            mlflow.log_metrics(
                {
                    "validation_error": float(error),
                    "validation_MAE": float(mae),
                    "validation_bias": float(bias),
                    "validation_PoissonDeviance": float(poisson),
                },
                step=step,
            )

        mlflow.log_metrics(
            {
                "CV_error_mean": float(np.mean(error_folds)),
                "CV_MAE_mean": float(np.mean(mae_folds)),
                "CV_bias_mean": float(np.mean(bias_folds)),
                "CV_PoissonDeviance_mean": float(np.mean(poisson_folds)),
            }
        )

        pipeline.fit(X, y)

        log_sklearn_model(
            sk_model=pipeline,
            name="model",
        )

        mlflow.set_tag(
            "Training Info",
            "XGBoost for SIGESGUARDA data",
        )

    return pipeline

if __name__ == "__main__":
    main()
