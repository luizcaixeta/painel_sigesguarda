# %%
import mlflow.pyfunc 
from modeling.data import db_url, load_gold_dataframe
from modeling.config import FEATURES

from sklearn.pipeline import Pipeline

import pandas as pd

from modeling.config import FEATURES, TARGET 

model = mlflow.pyfunc.load_model("models:/m-8a52ff93a1144b738a3df621d861947a")

df = load_gold_dataframe(db_url)

X = df.loc[:, FEATURES].head(250)

predicts = model.predict(X)

print(predicts)
# %%
