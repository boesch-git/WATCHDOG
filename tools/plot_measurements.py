# tools/plot_measurements.py
#
# Copyright (c) 2026 G. Aue, N. Diedrich. Licensed under the MIT License.
#


import argparse
import sqlite3
import matplotlib
from datetime import datetime
from pathlib import Path 

import matplotlib.pyplot as plt
import matplotlib.dates as mdates


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATABASE_PATH = PROJECT_ROOT / "data" / "watchdog.db"
DEFAULT_EXPORT_DIR = PROJECT_ROOT / "exports" 


def load_measurements(name, limit=None, latest=False):
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(f"Datenbank nicht gefunden du Oberpflaume: {DATABASE_PATH}")

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    query = """
    SELECT
        timestamp_utc,
        name,
        description,
        value,
        raw_value,
        unit
    FROM measurements
    WHERE name = ?
    """

    parameters = [name]

    if latest:
        query += " ORDER BY timestamp_utc DESC"
    else:
        query += " ORDER BY timestamp_utc ASC"

    if limit:
        query += " LIMIT ?"
        parameters.append(limit)

    rows = connection.execute(query, parameters).fetchall()
    connection.close()

    if latest:
        rows = list(reversed(rows))

    return rows


def parse_timestamp(timestamp_text):
    return datetime.fromisoformat(timestamp_text)


def create_plot(rows, name, output_path):
    if not rows:
        print(f"Keine Messwerde für '{name}' gefunden.")
        return

    timestamps = [parse_timestamp(row["timestamp_utc"]) for row in rows]
    values = [row["value"] for row in rows]

    description = rows[0]["description"] or name
    unit = rows[0]["unit"] or ""

    plt.figure(figsize=(12, 6))

    plt.plot(
        timestamps,
        values,
        marker="o",
        linewidth=1.5,
        markersize=3,
    )

    plt.title(f"WATCHDOG Trend: {description}")
    plt.xlabel("Zeit")
    plt.ylabel(f"Wert [{unit}]" if unit else "Wert")

    plt.grid(True)

    ax = plt.gca()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m.%Y %H:%M:%S")) #keine Ahnung, ob das mit %S als Sekunde so funktioniert
    plt.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150)
    plt.close()

    print(f"Diagramm erstellt: {output_path}")
    print(f"Geplottete Messwerte: {len(rows)}")


def build_default_output_path(name):
    safe_name = name.replace("/","_").replace("\\", "_").replace(" ", "_")
    return DEFAULT_EXPORT_DIR / f"{safe_name}_plot.png"


def main():
    parser = argparse.ArgumentParser(
        description="Erstellt ein Diagramm aus WatchDog-Messwerten."
    )

    parser.add_argument(
        "--name",
        required=True, 
        help="Name des Messpunktes, z.B. compressor1_current"
    )

    parser.add_argument(
        "--limit",
        type=int,
        help="Optionale maximale Anzahl Messwerte",
    )

    parser.add_argument(
        "--latest",
        action="store_true",
        help="Verwendet die neuesten Messwerte statt der ältesten.",
    )

    parser.add_argument(
        "--output",
        help="Optionaler Pfad zur PNG-Ausgabedatei.",
    )

    args = parser.parse_args()

    if args.output:
        output_path = Path(args.output)

        if not output_path.is_absolute():
            output_path = PROJECT_ROOT / output_path

    else:
        output_path = build_default_output_path(args.name)

    rows = load_measurements(
        name=args.name,
        limit=args.limit,
        latest=args.latest,
    )

    create_plot(
        rows=rows,
        name=args.name,
        output_path=output_path,
    )


if __name__ == "__main__":
    main()