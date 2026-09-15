import json
from pathlib import Path

import pandas as pd


DATA_DIR = Path("data")


def inspect_csv(filename):
    path = DATA_DIR / filename

    print("\n" + "=" * 70)
    print(filename)
    print("=" * 70)

    if not path.exists():
        print(f"FILE NOT FOUND: {path}")
        return None

    df = pd.read_csv(path)

    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")
    print("Column names:")

    for column in df.columns:
        print(f"  - {column}")

    print("\nFirst 3 rows:")
    print(df.head(3).to_string())

    return df


def inspect_json(filename):
    path = DATA_DIR / filename

    print("\n" + "=" * 70)
    print(filename)
    print("=" * 70)

    if not path.exists():
        print(f"FILE NOT FOUND: {path}")
        return None

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    print(f"Top-level type: {type(data).__name__}")

    if isinstance(data, dict):
        print(f"Number of keys: {len(data)}")
        print("First 10 keys:")

        for key in list(data.keys())[:10]:
            print(f"  - {key}")

    elif isinstance(data, list):
        print(f"Number of items: {len(data)}")

        if data:
            print("First item:")
            print(data[0])

    return data


def main():
    print("PHAGE-X DATASET INSPECTION")
    print("=" * 70)

    interactions = inspect_csv("phage_host_interactions.csv")
    loci = inspect_csv("esm2_embeddings_loci.csv")
    rbp = inspect_csv("esm2_embeddings_rbp.csv")
    rbpbase = inspect_csv("RBPbase.csv")

    inspect_json("Locibase.json")

    if interactions is not None:
        print("\n" + "=" * 70)
        print("INTERACTION DATA SUMMARY")
        print("=" * 70)

        for column in interactions.columns:
            print(
                f"{column}: "
                f"{interactions[column].nunique(dropna=True)} unique values"
            )

    if loci is not None:
        print("\n" + "=" * 70)
        print("LOCUS EMBEDDING ANALYSIS")
        print("=" * 70)

        numeric_columns = loci.select_dtypes(include="number").columns

        print(f"Shape: {loci.shape}")
        print(f"Numeric columns: {len(numeric_columns)}")

        if len(numeric_columns) > 0:
            print(f"Possible embedding dimension: {len(numeric_columns)}")

    if rbp is not None:
        print("\n" + "=" * 70)
        print("RBP EMBEDDING ANALYSIS")
        print("=" * 70)

        numeric_columns = rbp.select_dtypes(include="number").columns

        print(f"Shape: {rbp.shape}")
        print(f"Numeric columns: {len(numeric_columns)}")

        if len(numeric_columns) > 0:
            print(f"Possible embedding dimension: {len(numeric_columns)}")

    if rbpbase is not None:
        print("\n" + "=" * 70)
        print("RBPBASE ANALYSIS")
        print("=" * 70)

        print(f"Rows: {len(rbpbase)}")
        print("Columns:")

        for column in rbpbase.columns:
            print(f"  - {column}")

    print("\n" + "=" * 70)
    print("INSPECTION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
