import argparse 
import csv 
import os 
from pathlib import Path 
import psycopg
from psycopg.types.json import Jsonb 

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BRONZE_DIR = PROJECT_ROOT / "data" / "bronze"

def detect_delimiter(file_path: Path) -> str:
    with file_path.open("r", encoding="latin1", newline="") as file:
        sample = file.read(8192)
    
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";,")
        return dialect.delimiter 
    except csv.Error:
        return "," if "sigesguarda" in file_path.parts else ";"

def get_source(file_path: Path) -> str:
    return file_path.relative_to(BRONZE_DIR).parts[0]

def load_csv_to_bronze(conn: psycopg.Connection, source: str, file_path: Path) -> None:
    delimiter = detect_delimiter(file_path)

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO bronze.raw_files (
                source,
                file_name,
                file_path,
                file_size_bytes
            )
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (source, file_name)
            DO UPDATE SET 
                file_path = EXCLUDED.file_path,
                file_size_bytes = EXCLUDED.file_size_bytes,
                loaded_at = now()
            RETURNING id
            """,
            (source, file_path.name, str(file_path), file_path.stat().st_size),
        )

        raw_file_id = cur.fetchone()[0]

        cur.execute(
            "DELETE FROM bronze.raw_records WHERE raw_file_id = %s",
            (raw_file_id,),
        )

        with file_path.open("r", encoding="latin1", newline="") as file:
            reader = csv.DictReader(file, delimiter=delimiter)

            rows = [
                (raw_file_id, source, row_number, Jsonb(row))
                for row_number, row in enumerate(reader, start=1)
            ]
        
        if not rows:
            print(f"No records found: {file_path}")
            return 
        
        cur.executemany(
            """
            INSERT INTO bronze.raw_records (
                raw_file_id,
                source,
                row_number,
                payload
            )
            VALUES (%s, %s, %s, %s)
            """,
            rows,
        )
    print(f"Loaded {len(rows)} records from {file_path}")

def list_bronze_csv_files(source: str | None = None) -> list[Path]:
    if source:
        return sorted((BRONZE_DIR / source).glob("*.csv"))
    
    return sorted(BRONZE_DIR.glob("*/*.csv"))

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load bronze CSV files into PostgreSQL."
    )

    parser.add_argument(
        "--source",
        choices=["sigesguarda", "ibge2010", "ibge2022"],
        help="Load only one bronze source."
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
    
    files = list_bronze_csv_files(args.source)

    if not files:
        print("No bronze CSV files found.")
        return 
    
    with psycopg.connect(args.dsn) as conn:
        for file_path in files:
            source = get_source(file_path)
            load_csv_to_bronze(conn, source, file_path)
        
        conn.commit()

if __name__ == "__main__":
    main()