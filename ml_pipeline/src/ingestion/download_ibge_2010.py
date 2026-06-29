from pathlib import Path 
import shutil
import requests 
import zipfile 

PROJETCT_ROOT = Path(__file__).resolve().parents[3]
RAW_DIR = PROJETCT_ROOT / "data" / "bronze" / "ibge2010"

LINKS = {
    "censo2010_pr": "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2010/Resultados_do_Universo/Agregados_por_Setores_Censitarios/PR_20260615.zip"
}

REQUIRED_IBGE_2010_FILES = {
    "Basico_PR.csv",
    "PessoaRenda_PR.csv",
    "ResponsavelRenda_PR.csv",
    "Pessoa01_PR.csv",
    "Pessoa13_PR.csv",
    "Domicilio01_PR.csv"
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

def move_data_ibge_2010_files() -> None:
    base_dir = RAW_DIR / "censo2010_pr" / "Base informaçoes setores2010 universo PR"
    csv_dir = base_dir / "CSV"

    for file_path in csv_dir.glob("*.csv"):
        destination = RAW_DIR / file_path.name
        file_path.rename(destination)

def delete_ibge_2010_extracted_folder() -> None:
    extracted_dir = RAW_DIR / "censo2010_pr"

    shutil.rmtree(extracted_dir)

def delete_unused_ibge_2010_files() -> None:
    for file_path in RAW_DIR.iterdir():
        if not file_path.is_file():
            continue 

        if file_path.name in REQUIRED_IBGE_2010_FILES:
            continue 

        if file_path.name == ".gitkeep":
            continue 

        file_path.unlink()

def main() -> None:
    download_ibge_2010_data(LINKS)
    unzip_ibge_2010_data()
    move_data_ibge_2010_files()
    delete_ibge_2010_extracted_folder()
    delete_unused_ibge_2010_files()

if __name__ == "__main__":
    main()
