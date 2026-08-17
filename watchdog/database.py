# watchdog/database.py
#
# Copyright (c) 2026 G. Aue, N. Diedrich. Licensed under the MIT License.
#


import sqlite3
from pathlib import Path
from datetime import datetime, timezone

from watchdog.config import DATABASE_CONFIG


class WatchdogDatabase:
    def __init__(self):
        self.database_path = Path(DATABASE_CONFIG["path"])
        self.database_path.parent.mkdir(exist_ok=True)
        self.connection = None

    def connect(self):
        self.connection = sqlite3.connect(self.database_path)
        self.connection.execute("PRAGMA journal_mode=WAL;")
        self.connection.execute("PRAGMA synchronous=NORMAL;")
        self.create_tables()

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def create_tables(self):
        query = """
        CREATE TABLE IF NOT EXISTS measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp_utc TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            address INTEGER,
            register_type TEXT,
            raw_value REAL,
            value REAL,
            unit TEXT,
            source TEXT
        );
        """

        self.connection.execute(query)
        self.connection.commit()

    def insert_measurement(self, measurement, source):
        query = """
        INSERT INTO measurements (
            timestamp_utc,
            name,
            description,
            address,
            register_type,
            raw_value,
            value,
            unit,
            source
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """

        timestamp_utc = datetime.now(timezone.utc).isoformat()

        values = (
            timestamp_utc,
            measurement["name"],
            measurement.get("description"),
            measurement.get("address"),
            measurement.get("type"),
            measurement.get("raw_value"),
            measurement.get("value"),
            measurement.get("unit"),
            source,
        )

        self.connection.execute(query, values)

    def insert_measurements(self, measurements, source):
        for measurement in measurements.values():
            self.insert_measurement(measurement, source)

        self.connection.commit()