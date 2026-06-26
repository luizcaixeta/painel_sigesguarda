from pathlib import Path 
import requests 
import zipfile 

PROJETCT_ROOT = Path(__file__).resolve().parents[3]
RAW_DIR = PROJETCT_ROOT / "data" / "ibge2010" / "raw"

LINKS = {
    "censo2010_pr": "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2010/Resultados_do_Universo/Agregados_por_Setores_Censitarios/PR_20260615.zip"
}

def download_ibge_2010_data(links: dict[str, str]) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    for name, url in links.items():
        zip_path = RAW_DIR / f"{name}.zip"

        if zip_path.exists():
            print(f"File already exists: {zip_path.name}") 
            continue 

        print(f"Downloading {name}...")
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        zip_path.write_bytes(response.content)

def unzip_ibge_2010_data() -> None:
    for zip_path in RAW_DIR.glob("*.zip"):
        extract_dir = RAW_DIR / zip_path.stem 

        if extract_dir.exists():
            print(f"File already extracted: {extract_dir.name}")
            continue 

        extract_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as zip_file:
            zip_file.extractall(extract_dir)

        print(f"Extracted: {zip_path.name}")

        zip_path.unlink()

def main() -> None:
    download_ibge_2010_data(LINKS)
    unzip_ibge_2010_data()

if __name__ == "__main__":
    main()
