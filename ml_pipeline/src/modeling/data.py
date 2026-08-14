import os
from dotenv import load_dotenv

from sqlalchemy import create_engine, text
import pandas as pd

GOLD_QUERY = text("""
    SELECT 
        ommlf.*
    FROM gold.ocorrencias_mensais_ml_features AS ommlf
    INNER JOIN gold.load_batches AS lb
        ON lb.batch_id = ommlf.batch_id 
    WHERE 
        lb.is_current = true
    ORDER BY 
        ommlf.data,
        ommlf.bairro,
        ommlf.categoria
""")

load_dotenv()

user     = os.getenv("SIGESGUARDA_DATABASE.USER")
password = os.getenv("SIGESGUARDA_DATABASE.PASSWORD")
host     = os.getenv("SIGESGUARDA_DATABASE.HOST")
port     = os.getenv("SIGESGUARDA_DATABASE.PORT")
name     = os.getenv("SIGESGUARDA_DATABASE.NAME")

db_url = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{name}"

def load_gold_dataframe(db_url: str) -> pd.DataFrame:
    db_url = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{name}"

    engine = create_engine(db_url)

    with engine.connect() as conn:
        df = pd.read_sql_query(
            GOLD_QUERY,
            conn
        )

    return df
