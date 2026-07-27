# watchdog/main.py

import time
import logging

from watchdog.config import MODBUS_CONFIG
from watchdog.logger import setup_logger
from watchdog.modbus_client import WatchdogModbusClient


def run():
    setup_logger()

    logging.info("Watchdog wird gestartet.")
    logging.info("Modbus RTU Verbindung wird aufgebaut.")

    client = WatchdogModbusClient()

    if not client.connect():
        logging.error("Verbindung zum Modbus-Gerät fehlgeschlagen.")
        return

    logging.info("Modbus-Verbindung erfolgreich hergestellt.")

    try:
        while True:
            try:
                values = client.read_all_registers()

                for item in values.values():
                    logging.info(
                        "%s: %s %s raw=%s",
                        item["description"],
                        item["value"],
                        item["unit"],
                        item["raw_value"],
                    )

            except Exception as error:
                logging.error("Fehler beim Auslesen: %s", error)

            time.sleep(MODBUS_CONFIG["poll_interval_seconds"])

    except KeyboardInterrupt:
        logging.info("Watchdog wurde durch Benutzer beendet.")

    finally:
        client.close()
        logging.info("Modbus-Verbindung geschlossen.")
