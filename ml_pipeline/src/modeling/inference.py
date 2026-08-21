# %%
import mlflow.pyfunc 
from modeling.data import SQL_DIR, read_sql, load_sql_into_dataframe
from modeling.config import FEATURES

from sklearn.pipeline import Pipeline

import pandas as pd

from modeling.config import FEATURES, TARGET 

GOLD_QUERY = read_sql(SQL_DIR, 'load_gold_data', 'gold_query.sql')

model = mlflow.pyfunc.load_model("models:/m-8a52ff93a1144b738a3df621d861947a")

df = load_sql_into_dataframe(GOLD_QUERY)

X = df.loc[:, FEATURES].head(250)

predicts = model.predict(X)

print(predicts)
# %%
