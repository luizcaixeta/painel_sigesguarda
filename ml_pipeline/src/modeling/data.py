import os
from dotenv import load_dotenv

from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine 
from sqlalchemy.sql.elements import TextClause
import pandas as pd

load_dotenv()
 
user     = os.getenv("SIGESGUARDA_DATABASE.USER")
password = os.getenv("SIGESGUARDA_DATABASE.PASSWORD")
host     = os.getenv("SIGESGUARDA_DATABASE.HOST")
port     = os.getenv("SIGESGUARDA_DATABASE.PORT")
name     = os.getenv("SIGESGUARDA_DATABASE.NAME")

db_url = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{name}"

SQL_DIR = Path(__file__).parent / 'sql'

def read_sql(
        sql_dir:  str | Path,
        folder: str,
        filename: str,
    ) -> TextClause:

    sql_path = Path(sql_dir) / folder / filename
    return text(sql_path.read_text(encoding='utf-8'))

def load_sql_into_dataframe(read_query: TextClause) -> pd.DataFrame:

    engine = create_engine(db_url)

    with engine.connect() as conn:
        df = pd.read_sql_query(
            read_query,
            conn,
            parse_dates=["data"],
        )

    return df
