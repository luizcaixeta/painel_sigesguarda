import argparse
import os
import re
import unicodedata

import psycopg
from psycopg.types.json import Jsonb
import requests

LAYER_URL = (
    "https://geocuritiba.ippuc.org.br/server/rest/services/"
    "GeoCuritiba/Publico_Interno_GeoCuritiba_BaseCartografica_para_BC/"
    "MapServer/44"
)

BAIRRO_ID_OVERRIDES = {
    "alto da rua xv": "alto-da-xv",
    "campo de santana": "campo-do-santana",
    "cidade industrial de curitiba": "cidade-industrial",
}

def normalize_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip().lower())
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", " ", normalized).strip()

def make_bairro_id(name: str) -> str:
    normalized = normalize_name(name)
    return BAIRRO_ID_OVERRIDES.get(normalized, normalized.replace(" ", "-"))

def load_features() -> list[dict]:
    response = requests.get(
        f"{LAYER_URL}/query",
        params={
            "where": "1=1",
            "outFields": "codigo,nome",
            "returnGeometry": "true",
            "outSR": "4326",
            "f": "geojson",
        },
        timeout=60,
    )
    response.raise_for_status()

    return response.json()["features"]

def load_dim_bairros(conn: psycopg.Connection, features: list[dict]) -> None:
    rows = []

    for feature in features:
        properties = feature["properties"]
        name = properties["nome"].strip()

        rows.append(
            (
                make_bairro_id(name),
                int(properties["codigo"]),
                name,
                Jsonb(feature["geometry"]),
                LAYER_URL,
            )
        )

    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO gold.dim_bairros (
                bairro_id,
                codigo_ippuc,
                nome,
                geometry_,
                geometry_source
            )
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (bairro_id)
            DO UPDATE SET
                codigo_ippuc = EXCLUDED.codigo_ippuc,
                nome = EXCLUDED.nome,
                geometry_ = EXCLUDED.geometry_,
                geometry_source = EXCLUDED.geometry_source
            """,
            rows,
        )

    print(f"Loaded {len(rows)} neighborhoods into gold.dim_bairros.")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load Curitiba neighborhoods into gold.dim_bairros."
    )
    parser.add_argument(
        "--dsn",
        default=os.getenv("SIGESGUARDA_DB_DSN"),
        help="PostgreSQL DSN. Defaults to SIGESGUARDA_DB_DSN.",
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()

    if not args.dsn:
        raise RuntimeError(
            "Database DSN not provided. Set SIGESGUARDA_DB_DSN or use --dsn."
        )

    features = load_features()

    with psycopg.connect(args.dsn) as conn:
        load_dim_bairros(conn, features)
        conn.commit()

if __name__ == "__main__":
    main()
