import argparse

from gold.ml_features import (
    build_gold_datasets,
    write_gold,
    write_socioeconomic_gold,
)

def main() -> None:
    parser = argparse.ArgumentParser(description="Build Gold datasets.")
    parser.add_argument(
        "--source",
        choices=["all", "ml_features", "socioeconomic_features"],
        default="all",
        help="Build all Gold datasets or only the selected dataset.",
    )
    args = parser.parse_args()

    datasets = build_gold_datasets(args.source)

    if "ml_features" in datasets:
        output = write_gold(datasets["ml_features"])
        print(f"Gold ML features generated in {output}")

    if "socioeconomic_features" in datasets:
        output = write_socioeconomic_gold(datasets["socioeconomic_features"])
        print(f"Gold socioeconomic features generated in {output}")


if __name__ == "__main__":
    main()
