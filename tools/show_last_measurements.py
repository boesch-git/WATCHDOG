# tools/show_last_measurements.py
#
# Copyright (c) 2026 G. Aue, N. Diedrich. Licensed under the MIT License.
#


import sqlite3
from pathlib import Path

DATABASE_PATH = Path("../data/watchdog.db")

def main():
    if not DATABASE_PATH.exists():
        print ("Database not found - you may want to create one.")
        return

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    query = """
    SELECT
        id,
        timestamp_utc,
        name, 
        value,
        unit,
        raw_value,
        source
    FROM measurements
    ORDER BY id DESC
    LIMIT 20;
    """

    rows = connection.execute(query).fetchall()

    if not rows:
        print("No values found in database!")
        return

    for row in rows:
        print(
            f"{row['id']} | {row['timestamp_utc']} | "
            f"{row['name']} = {row['value']} {row['unit']}"
            f"(raw={row['raw_value']}, source={row['source']})"
        )

    connection.close()

if __name__ == "__main__":
    main()