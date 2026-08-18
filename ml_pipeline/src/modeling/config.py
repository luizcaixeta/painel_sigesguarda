FEATURES_NUMERICAS = [
    "log1p_lag_1",
    "log1p_lag_2",
    "log1p_lag_3",
    "log1p_lag_6",
    "log1p_lag_12",
    "log1p_media_3",
    "log1p_media_6",
    "log1p_media_12",
    "iqv",
    "log_pop",
    "tempo",
    "mes_sin_1",
    "mes_cos_1",
    "mes_sin_2",
    "mes_cos_2",
]

FEATURES_CATEGORICAS = ["bairro", "categoria"]
FEATURES = FEATURES_NUMERICAS + FEATURES_CATEGORICAS
TARGET = "y"

params = {
    "objective": "count:poisson",
    "n_estimators": 500,
    "learning_rate": 0.03,
    "max_depth": 4,
    "min_child_weight": 10,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "reg_alpha": 0.1,
    "reg_lambda": 1.0,
    "tree_method": "hist",
    "random_state": 42,
    "n_jobs": -1,
}
