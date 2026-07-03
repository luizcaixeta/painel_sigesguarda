import argparse

from common import write_silver
from ibge_2010 import build_silver as build_ibge2010_silver
from ibge_2022 import build_silver as build_ibge2022_silver
from sigesguarda import build_silver as build_sigesguarda_silver

def main() -> None:
    parser = argparse.ArgumentParser(description="Build all silver datasets.")
    parser.add_argument(
        "--source",
        choices=["all", "sigesguarda", "ibge", "ibge2010", "ibge2022"],
        default="all",
    )
    args = parser.parse_args()

    if args.source in {"all", "sigesguarda"}:
        output = write_silver(
            build_sigesguarda_silver(),
            "sigesguarda/base_unificada.parquet",
        )
        print(f"SIGESGUARDA silver generated in {output}")

    if args.source in {"all", "ibge", "ibge2010"}:
        output = write_silver(
            build_ibge2010_silver(),
            "ibge2010/base_bairros_2010.parquet",
        )
        print(f"IBGE 2010 silver generated in {output}")

    if args.source in {"all", "ibge", "ibge2022"}:
        output = write_silver(
            build_ibge2022_silver(),
            "ibge2022/base_bairros_2022.parquet",
        )
        print(f"IBGE 2022 silver generated in {output}")

if __name__ == "__main__":
    main()
