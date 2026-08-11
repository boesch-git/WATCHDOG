#watchdog/main.py

import logging
import time

from watchdog.config import MODBUS_CONFIG
from watchdog.database import WatchdogDatabase
from watchdog.logger import setup_logger
from watchdog.modbus_client import WatchdogModbusClient

def wait_interruptible(seconds):
    # """
    # Wartet die angegebene Anzahl Sekunden.

    # Die Wartezeit wird in Ein-Sekunden-Schritten durchgeführt, damit das Programm mit Strg+C schnell beendet werden kann. 
    # """
    for _ in range(seconds):
        time.sleep(1)


def log_communication_error(error):
    # """
    # Gibt eine Fehlermeldung abhängig vom aufgetretenen Fehlertyp aus. 
    # """
    error_type = type(error).__name__
    error_message = str(error) or "Keine zusätzliche Fehlerbeschreibung"

    logging.error(
        "Kommunikationsfehler erkannt | Typ: %s | Meldung: %s",
        error_type,
        error_message,
    )

    message_lower = error_message.lower()
    #permission denied
    if "permission denied" in message_lower:
        logging.error(
            "Keine Berechtigung für die serielle Schnittstelle."
            "prüfe die Mitgliedschaft in der Gruppe 'dialout'."
        )

    #no such file
    elif "no such file" in message_lower:
        logging.error(
            "Die konfigurierte serielle Schnittstelle wurde nicht gefunden: %s",
            MODBUS_CONFIG["port"],
        )

    #port not able to being open
    elif "could not open port" in message_lower:
        logging.error(
            "Der serielle Port %s konnte nicht geöffnet werden. "
            "Möglicherweise wurde der Adapter entfernt oder der Port wird von einem anderen Programm verwendet. ",
            MODBUS_CONFIG["port"],
        )
            

    #timeout or no response 
    elif "timeout" in message_lower or "no response" in message_lower:
        logging.error(
            "Die Anlage antwortet nicht. "
            "Prüfe Slave-ID, Baudrate, Parität, Registeradresse, Terminierung oder RS485-Verkabelung. "
        )

    #crc or checksum error
    elif "crc" in message_lower or "checksum" in message_lower:
        logging.error(
            "Es wurde ein fehlerhaftes Modbus-Telegram empfangen. "
            "Prüfe Verkabelung, Schirmung, Abschlusswiderstände und serielle Parameter. "
        )

    #illegal address
    elif "illegal address" in message_lower:
        logging.error(
            "Der Regler meldet eine ungültige Registeradresse. "
            "Prüfe Registertyp und nullbasierte Adressierung. "
        )

    #illegal function
    elif "illegal function" in message_lower:
        logging.error(
            "Der Regler unterstützt die verwendete Modbus-Funktion nicht. "
            "Prüfe, ob Holding Register oder Input Register gelesen werden müssen. "
        )


def run():
    setup_logger()

    reconnect_interval = MODBUS_CONFIG["reconnect_interval_seconds"]
    poll_interval = MODBUS_CONFIG["poll_interval_seconds"]

    logging.info("=" * 60)
    logging.info("Watchdog wird gestartet.")
    logging.info("Modbus RTU Port: %s", MODBUS_CONFIG["port"])
    logging.info("Baudrate: %s", MODBUS_CONFIG["baudrate"])
    logging.info("Parität: %s", MODBUS_CONFIG["parity"])
    logging.info("Slave-ID: %s", MODBUS_CONFIG["slave_id"])
    logging.info("Abfrageintervall: %s Sekunden", poll_interval)
    logging.info("Wiederverbindungsintervall: %s Sekunden", reconnect_interval)
    logging.info("=" * 60)

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
                logging.info(
                    "Öffne Modbus-Verbindung über %s ...",
                    MODBUS_CONFIG["port"],
                )

                if not client.connect():
                    raise ConnectionError(
                        f"Serieller Port {MODBUS_CONFIG['port']} "
                        "konnte nicht geöffnet werden."
                    )

                logging.info(
                    "Serieller Port wurde geöffnet. "
                    "Teste die Kommunikation mit dem Modbus-Regler."
                )

                first_successful_read = True

                while True:
                    values = client.read_all_registers()

                    if first_successful_read:
                        logging.info(
                            "Modbus-Kommunikation erfolgreich. "
                            "Der Regler antwortet."
                        )
                        first_successful_read = False

                    database.insert_measurements(
                        measurements=values,
                        source=MODBUS_CONFIG["port"],
                    )

                    for item in values.values():
                        logging.info(
                            "%s | Adresse %s | Wert: %s %s | "
                            "Rohwert: %s | gespeichert",
                            item["description"],
                            item["address"],
                            item["value"],
                            item["unit"],
                            item["raw_value"],
                        )

                    wait_interruptible(poll_interval)

            except KeyboardInterrupt:
                raise

            except Exception as error:
                log_communication_error(error)

                logging.warning(
                    "Modbus-Verbindung wird geschlossen."
                )

                client.close()

                logging.warning(
                    "Neuer Verbindungsversuch in %s Sekunden.",
                    reconnect_interval,
                )

                wait_interruptible(reconnect_interval)

                logging.info(
                    "Wartezeit beendet. Starte neuen Verbindungsversuch."
                )

    except KeyboardInterrupt:
        logging.info(
            "Watchdog wurde durch den Benutzer beendet."
        )

    except Exception as error:
        logging.critical(
            "Nicht behebbarer Programmfehler | Typ: %s | Meldung: %s",
            type(error).__name__,
            error,
        )

    finally:
        client.close()
        database.close()

        logging.info("Modbus-Port geschlossen.")
        logging.info("Datenbank geschlossen.")
        logging.info("Watchdog wurde beendet.")

    #     while True:
    #         try:
    #             values = client.read_all_registers()

    #             database.insert_measurements(
    #                 measurements=values,
    #                 source=MODBUS_CONFIG["port"],
    #             )

    #             for item in values.values():
    #                 logging.info(
    #                     "%s | Adresse %s | Wert: %s %s | Rohwert: %s | gespeichert",
    #                     item["description"],
    #                     item["address"],
    #                     item["value"],
    #                     item["unit"],
    #                     item["raw_value"],
    #                 )

    #         except Exception as error:
    #             logging.error("Fehler beim Auslesen oder Speichern: %s", error)

    #         time.sleep(MODBUS_CONFIG["poll_interval_seconds"])

    # except KeyboardInterrupt:
    #     logging.info("Watchdog wurde durch Benutzer beendet.")

    # finally:
    #     client.close()
    #     database.close()
    #     logging.info("Modbus-Port und Datenbank geschlossen.")
