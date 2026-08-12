from pathlib import Path 
import shutil
import requests 
import zipfile 

PROJETCT_ROOT = Path(__file__).resolve().parents[3]
RAW_DIR = PROJETCT_ROOT / "data" / "bronze" / "ibge2022"

LINKS = {
    "agregados_bairros_basico": "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/Agregados_por_Bairro_csv/Agregados_por_bairros_basico_BR_20260520.zip",
    "agregados_bairros_alfabetizacao": "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/Agregados_por_Bairro_csv/Agregados_por_bairros_alfabetizacao_BR.zip",
    "agregados_bairros_domicilio1": "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/Agregados_por_Bairro_csv/Agregados_por_bairros_caracteristicas_domicilio1_BR.zip",
    "agregados_bairros_domicilio2": "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/Agregados_por_Bairro_csv/Agregados_por_bairros_caracteristicas_domicilio2_BR_20250417.zip",
    "agregados_bairros_renda_responsavel": "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios_Rendimento_do_Responsavel/Agregados_por_bairros_renda_responsavel_BR_20260508_csv.zip"
}

REQUIRED_IBGE_2022_FILES = {
    "Agregados_por_bairros_basico_BR.csv",
    "Agregados_por_bairros_alfabetizacao_BR.csv",
    "Agregados_por_bairros_renda_responsavel_BR.csv",
    "Agregados_por_bairros_caracteristicas_domicilio1_BR.csv",
    "Agregados_por_bairros_caracteristicas_domicilio2_BR.csv",
}

def download_ibge_2022_data(links: dict[str, str]) -> None:
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

def unzip_ibge_2022_data() -> None:
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

def move_data_ibge_2022_files() -> None:
    for file_path in RAW_DIR.rglob("*.csv"):
        if file_path.parent == RAW_DIR:
            continue 

        if file_path.name not in REQUIRED_IBGE_2022_FILES:
            continue 

        destination = RAW_DIR / file_path.name 
        file_path.rename(destination)

def delete_ibge_2022_extracted_folders() -> None:
    for path in RAW_DIR.iterdir():
        if path.is_dir():
            shutil.rmtree(path)

def delete_unused_ibge_2022_files() -> None:
    for file_path in RAW_DIR.iterdir():
        if not file_path.is_file():
            continue 

        if file_path.name in REQUIRED_IBGE_2022_FILES:
            continue 

        if file_path.name == ".gitkeep":
            continue 

        file_path.unlink()

def main() -> None:
    download_ibge_2022_data(LINKS)
    unzip_ibge_2022_data()
    move_data_ibge_2022_files()
    delete_ibge_2022_extracted_folders()
    delete_unused_ibge_2022_files()

if __name__ == "__main__":
    main()
