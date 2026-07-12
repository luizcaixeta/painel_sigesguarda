import argparse

from ml_features import build_gold, write_gold

def main() -> None:
    parser = argparse.ArgumentParser(description="Build gold ML feature datasets.")
    parser.add_argument(
        "--source",
        choices=["all", "ml_features"],
        default="all",
        help="Build all gold datasets or only the ML features dataset.",
    )
    parser.parse_args()

    output = write_gold(build_gold())
    print(f"Gold ML features generated in {output}")

if __name__ == "__main__":
    main()

