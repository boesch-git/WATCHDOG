#watchdog/main.py

import logging
import time

from watchdog.config import MODBUS_CONFIG
from watchdog.database import WatchdogDatabase
from watchdog.logger import setup_logger
from watchdog.modbus_client import WatchdogModbusClient


def run():
    setup_logger()

    logging.info("Watchdog wird gestartet.")
    logging.info("Modbus RTU Port: %s", MODBUS_CONFIG["port"])
    logging.info("Baudrate: %s", MODBUS_CONFIG["baudrate"])
    logging.info("Slave-ID: %s", MODBUS_CONFIG["slave_id"])

    client = WatchdogModbusClient()
    database = WatchdogDatabase()

    try:
        database.connect()
        logging.info("Datenbank erfolgreich geöffnet.")

        if not client.connect():
            logging.error("Modbus-Port konnte nicht geöffnet werden.")
            return

        logging.info("Modbus-Port erfolgreich geöffnet.")

        while True:
            try:
                values = client.read_all_registers()

                database.insert_measurements(
                    measurements=values,
                    source=MODBUS_CONFIG["port"],
                )

                for item in values.values():
                    logging.info(
                        "%s | Adresse %s | Wert: %s %s | Rohwert: %s | gespeichert",
                        item["description"],
                        item["address"],
                        item["value"],
                        item["unit"],
                        item["raw_value"],
                    )

            except Exception as error:
                logging.error("Fehler beim Auslesen oder Speichern: %s", error)

            time.sleep(MODBUS_CONFIG["poll_interval_seconds"])

    except KeyboardInterrupt:
        logging.info("Watchdog wurde durch Benutzer beendet.")

    finally:
        client.close()
        database.close()
        logging.info("Modbus-Port und Datenbank geschlossen.")
