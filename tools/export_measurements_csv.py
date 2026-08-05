# tools/export_measurements_csv.py

import argparse
import csv
import sqlite3
from pathlib import Path 

# TODO: Pfade prüfen, ob die relativ oder absolut angegeben werden müssen, insbesondere für den Fieldtest
# DATABASE_PATH = Path("data/watchdog.db")
# DEFAULT_OUTPUT_PATH = Path("exports/measurements_export.csv")

# robustere Pfade:
PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATABASE_PATH = PROJECT_ROOT / "data" / "watchdog.db"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "exports" / "measurements_export.csv"

#debug test print("TESTESTESTEST - DATABASE_PATH", DATABASE_PATH)

def build_query(name=None, limit=None, latest=False):
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
#debug test    print("query1:", query)

    parameters = []

    if name: 
        query += " WHERE name = ?"
        parameters.append(name)

    if latest:
        query += " ORDER BY timestamp_utc DESC"
    else:
        query+= " ORDER BY timestamp_utc ASC"

    if limit:
        query += " LIMIT ?"
        parameters.append(limit)

#debug test    print ("TESTSETSET - query:", query)
    return query, parameters

def export_measurements(output_path, name=None, limit=None, latest=False):
    if not DATABASE_PATH.exists():
        print("Die Datenbank fehlt, Du Eumel! Ich kann hier nichts finden: ", DATABASE_PATH)
        return

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

#debug test    print("output_path", output_path)

    query, parameters = build_query(
        name=name,
        limit=limit,
        latest=latest,
    )

    rows = connection.execute(query, parameters).fetchall()

    if latest:
        rows = list(reversed(rows))

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
    print(f"Exportierte Zeilen: {len(rows)}")


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
    parser.add_argument (
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help="Pfad zur CSV-Ausgabedatei",
    )

    parser.add_argument(
        "--latest",
        action="store_true",
        help="Exportiert die neuesten Messwerte anstatt der ältesten.",
    )


    args = parser.parse_args()

    export_measurements(
        output_path=args.output,
        name=args.name,
        limit=args.limit,
        latest=args.latest,
    )

if __name__ == "__main__":
    main()