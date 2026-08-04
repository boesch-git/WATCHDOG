# tools/list_measurement_names.py

import sqlite3
from pathlib import Path

DATABASE_PATH = Path("../data/watchdog.db")

def main():
    if not DATABASE_PATH.exists():
        print("Datenbank existiert nicht:", DATABASE_PATH)
        return

    connection = sqlite3.connect(DATABASE_PATH)

    query = """

    SELECT
        name, 
        description, 
        unit, 
        COUNT(*) AS count,
        MIN(timestamp_utc) AS first_timestamp,
        MAX(timestamp_utc) AS last_timestamp
    FROM measurements
    GROUP BY name, description, unit
    ORDER BY name;
    """

    rows = connection.execute(query).fetchall()

    if not rows:
        print("Keine Messwerte gefunden.")
        connection.close()
        return

    print("Verfügbare Messpunkte:")
    print()

    for row in rows:
        name, description, unit, count, first_timestamp, last_timestamp = row

        print(f"Name:           {name}")
        print(f"Beschreibung:   {description}")
        print(f"Einheit:        {unit}")
        print(f"Anzahl:         {count}")
        print(f"Von:            {first_timestamp}")
        print(f"Bis:            {last_timestamp}")
        print("-" * 60)

    connection.close()

if __name__ == "__main__":
    main()