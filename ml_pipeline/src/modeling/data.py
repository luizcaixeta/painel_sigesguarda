import os
from dotenv import load_dotenv

from sqlalchemy import create_engine, text
import pandas as pd

GOLD_QUERY = text("""
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
            conn,
            parse_dates=["data"],
        )

    return df
