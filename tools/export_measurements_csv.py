# tools/export_measurement_csv.py

import argparse
import csv
import sqlite3
from pathlib import Path 

DATABASE_PATH = Path("../data/watchdog.db")
DEFAULT_OUTPUT_PATH = Path("../exports/measurements_export.csv")

def build_query(name=None, limit=None):
    query = """
    SELECT
        id, 
        timestamp_utc,
        name,
        description, 
        address, 
        register_type,
        raw_value,
        value,
        unit,
        source
    FROM measurements
    """

    parameters = []

    if name: 
        query += " WHERE name = ?"
        parameters.append(name)

    query += " ORDER BY timestamp_utc ASC"

    if limit:
        query += " LIMIT ?"
        parameters.append(limit)

    return query, parameters

def export_measurements(outpunt_path, name=None, limit=None):
    if not DATABASE_PATH.exists():
        print("Die Datenbank fehlt, Du Eumel! Ich kann hier nichts finden: ", DATABASE_PATH)
        return

    output_path = Path(output_path)
    output_path.parent.mkdir(exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    query, parameters = build_query(name=name, limit=limit)
    rows = connection.execute(query, parameters).fetchall()

    if not rows:
        print("Keine passenden Messwerte gefunden.")
        connection.close()
        return

    fieldnames = rows[0].keys()

    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()

        for row in rows:
            writer.writerow(dict(row))

    connection.close()

    print(f"CSV-Export abgeschlossen: {output_path}")
    print(f"Exportierte Zeilen: {len:(rows)}")

def main():
    parser = argparse.ArgumentParser(
        description="Exportiert Watchdog-Messwerte aus SQLite als CSV."
    )

    parser.add_argument(
        "--name",
        help="Optionaler Messpunktname, z.B. stromaufnahme_verdichter",
    )

    parser.add_argument(
        "--limit",
        type=int,
        help="Optionale maximale Anzahl exportierter Zeilen.",
    )


    args = parser.parse_args()

    export_measurements(
        output_path=args.output,
        name=args.name,
        limit=args.limit,
    )

    if __name__ == "__main__":
        main()