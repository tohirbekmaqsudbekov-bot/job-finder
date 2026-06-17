import csv
import json
from pathlib import Path


def csv_to_json(csv_path: Path, json_path: Path, encoding: str = "utf-8-sig", delimiter: str = ","):
    rows = []
    with csv_path.open("r", encoding=encoding, newline="") as csv_file:
        reader = csv.DictReader(csv_file, delimiter=delimiter)
        
        for row in reader:
            clean_row = {}
            for key, value in row.items():
                # Agar key None bo'lsa (qo'shimcha qiymatlar) - o'tkazib yuboramiz
                if key is None:
                    continue
                
                clean_key = key.strip()
                if not clean_key:
                    continue
                
                # Value list bo'lishi mumkin (qo'shimcha qiymatlar bo'lganida)
                if isinstance(value, list):
                    clean_value = ", ".join(v.strip() for v in value if v)
                elif value is None:
                    clean_value = ""
                else:
                    clean_value = value.strip()
                
                clean_row[clean_key] = clean_value
            rows.append(clean_row)

    json_path.parent.mkdir(parents=True, exist_ok=True)
    with json_path.open("w", encoding="utf-8") as json_file:
        json.dump(rows, json_file, ensure_ascii=False, indent=2)

    print(f"{len(rows)} ta qator {csv_path.name} -> {json_path.name} ga o'tkazildi")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Convert a CSV file to JSON.")
    parser.add_argument("--csv", default="5.csv", help="Path to the input CSV file.")
    parser.add_argument("--json", default="5.json", help="Path to the output JSON file.")
    parser.add_argument("--encoding", default="utf-8-sig", help="File encoding.")
    parser.add_argument("--delimiter", default=",", help="CSV field delimiter.")
    args = parser.parse_args()

    csv_to_json(Path(args.csv), Path(args.json), args.encoding, args.delimiter)