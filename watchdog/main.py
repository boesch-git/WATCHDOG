#watchdog/main.py

import logging
import time

from watchdog.config import MODBUS_CONFIG
from watchdog.logger import setup_logger
from watchdog.modbus_client import WatchdogModbusClient


def run():
    setup_logger()

    logging.info("Watchdog wird gestartet.")
    logging.info("Modbus RTU Port: %s", MODBUS_CONFIG["port"])
    logging.info("Baudrate: %s", MODBUS_CONFIG["baudrate"])
    logging.info("Slave-ID: %s", MODBUS_CONFIG["slave_id"])

    client = WatchdogModbusClient()

    if not client.connect():
        logging.error("Modbus-Port konnte nicht geöffnet werden.")
        return

    logging.info("Modbus-Port erfolgreich geöffnet.")

    try:
        while True:
            try:
                values = client.read_all_registers()

                for item in values.values():
                    logging.info(
                        "%s | Adresse %s | Wert: %s %s | Rohwert: %s",
                        item["description"],
                        item["address"],
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
        logging.info("Modbus-Port geschlossen.")
