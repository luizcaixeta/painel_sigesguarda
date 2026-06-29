import json
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
import requests
import argparse 

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_DIR = PROJECT_ROOT / "data" / "SIGESGUARDA" / "raw"
STATE_FILE = RAW_DIR / "download_state.json"

SIGESGUARDA_DATASET_KEY = "b16ead9d-835e-41e8-a4d7-dcc4f2b4b627"
SIGESGUARDA_CSV_FORMAT_KEY = "377f4e23-0e4f-4f11-954f-ae06ba689558"

DOWNLOAD_LIST_URL = "https://dadosabertos.curitiba.pr.gov.br/ConjuntoDado/DownloadArquivos/"
HISTORICAL_URL = "http://dadosabertos.c3sl.ufpr.br/curitiba/Sigesguarda/2024-02-01_sigesguarda_-_Base_de_Dados.csv"
HISTORICAL_FILE = "2024-02-01_sigesguarda_-_Base_de_Dados.csv"

@dataclass(frozen=True)
class SigesguardaFile:
    url: str
    filename: str
    portal_updated_at: str
    portal_size: str

class DownloadTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[dict[str, str | list[str]]]] = []
        self.current_row: list[dict[str, str | list[str]]] = []
        self.current_links: list[str] = []
        self.current_text: list[str] = []
        self.in_row = False
        self.in_cell = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self.in_row = True
            self.current_row = []
            return

        if tag == "td" and self.in_row:
            self.in_cell = True
            self.current_links = []
            self.current_text = []
            return

        if tag != "a" or not self.in_cell:
            return

        attrs_dict = dict(attrs)
        href = attrs_dict.get("href")

        if href:
            self.current_links.append(href)

    def handle_data(self, data: str) -> None:
        if self.in_cell:
            self.current_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "td" and self.in_cell:
            self.current_row.append(
                {
                    "text": "".join(self.current_text).strip(),
                    "links": self.current_links.copy(),
                }
            )
            self.in_cell = False
            return

        if tag == "tr" and self.in_row:
            if self.current_row:
                self.rows.append(self.current_row)
            self.in_row = False

def get_filename_from_url(url: str) -> str:
    return Path(urlparse(url).path).name

def load_download_state() -> dict[str, str]:
    if not STATE_FILE.exists():
        return {}

    return json.loads(STATE_FILE.read_text(encoding="utf-8"))

def save_download_state(latest_file: SigesguardaFile) -> None:
    state = {
        "latest_file": latest_file.filename,
        "latest_url": latest_file.url,
        "portal_updated_at": latest_file.portal_updated_at,
        "portal_size": latest_file.portal_size,
        "downloaded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }

    STATE_FILE.write_text(
        json.dumps(state, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

def parse_portal_datetime(value: str) -> datetime:
    return datetime.strptime(value, "%d/%m/%Y %H:%M")

def get_latest_sigesguarda_file() -> SigesguardaFile:
    response = requests.get(
        DOWNLOAD_LIST_URL,
        params={
            "conjuntoDadoChave": SIGESGUARDA_DATASET_KEY,
            "conjuntoDadoExtensao": SIGESGUARDA_CSV_FORMAT_KEY,
            "pagina": 1,
            "tamanhoPagina": 50,
        },
        timeout=60,
    )
    response.raise_for_status()

    data = response.json()
    if not data.get("sucesso"):
        raise RuntimeError(data.get("erro") or "Failed to list SIGESGUARDA files.")

    parser = DownloadTableParser()
    parser.feed(data["tabela"])

    files = []

    for row in parser.rows:
        if len(row) < 4:
            continue 
        
        links = row[0]["links"]
        if not isinstance(links, list) or not links:
            continue 

        url = str(links[0])
        if not url.endswith("_sigesguarda_-_Base_de_Dados.csv"):
            continue 

        files.append(
            SigesguardaFile(
                url=url,
                filename=get_filename_from_url(url),
                portal_updated_at=str(row[2]["text"]),
                portal_size=str(row[3]["text"])
            )
        )

    if not files:
        raise RuntimeError("No SIGESGUARDA CSV links found.")
    
    return max(files, key=lambda file: parse_portal_datetime(file.portal_updated_at))

def get_latest_sigesguarda_url() -> str:
    return get_latest_sigesguarda_file().url

def has_new_sigesguarda_file(latest_file: SigesguardaFile) -> bool:
    state = load_download_state()
    latest_state = {
        "latest_file": latest_file.filename,
        "latest_url": latest_file.url,
        "portal_updated_at": latest_file.portal_updated_at,
        "portal_size": latest_file.portal_size,
    }

    return any(state.get(key) != value for key, value in latest_state.items())

def download_file(url: str, output_dir: Path = RAW_DIR, force: bool = False) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = get_filename_from_url(url)
    destination = output_dir / filename

    if destination.exists() and not force:
        print(f"File already exists: {destination.name}")
        return destination

    print(f"Downloading: {filename}")
    temp_destination = destination.with_suffix(destination.suffix + ".tmp")

    with requests.get(url, stream=True, timeout=120) as response:
        response.raise_for_status()

        with temp_destination.open("wb") as file:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    file.write(chunk)

    temp_destination.replace(destination)
    return destination

def delete_unused_sigesguarda_files(latest_filename: str) -> None:
    keep_files = {
        ".gitkeep",
        STATE_FILE.name,
        HISTORICAL_FILE,
        latest_filename,
    }

    for file_path in RAW_DIR.iterdir():
        if not file_path.is_file():
            continue

        if file_path.name in keep_files:
            continue

        file_path.unlink()
        print(f"Deleted: {file_path.name}")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download SIGESGUARDA raw data when a newer file is available."
    )

    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check if a newer SIGESGUARDA file is available.",
    )

    return parser.parse_args()

def main() -> None:
    args = parse_args()

    latest_file_info = get_latest_sigesguarda_file()
    has_update = has_new_sigesguarda_file(latest_file_info)

    if args.check_only:
        if has_update:
            print("New SIGESGUARDA file available:"
                  f"{latest_file_info.filename} "
                  f"updated at {latest_file_info.portal_updated_at}, size {latest_file_info.portal_size}"
            )
        else:
            print(f"No new SIGESGUARDA file available: {latest_file_info.filename}")
        
        return 

    if not has_update:
        print(f"No new SIGESGUARDA file available: {latest_file_info.filename}")
        return 
    
    download_file(HISTORICAL_URL)
    latest_file = download_file(latest_file_info.url, force=True)

    delete_unused_sigesguarda_files(latest_file.name)
    save_download_state(latest_file_info)

    print(f"Downloaded latest SIGESGUARDA file: {latest_file.name}")

if __name__ == "__main__":
    main()
