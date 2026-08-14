import logging
import time
from pathlib import Path

from watchdog.config import MODBUS_CONFIG
from watchdog.database import WatchdogDatabase
from watchdog.logger import setup_logger
from watchdog.modbus_client import WatchdogModbusClient


def wait_interruptible(seconds):
    """
    Wartet in kurzen Schritten, damit Watchdog während der Wartezeit
    mit Strg+C beendet werden kann.
    """
    end_time = time.monotonic() + float(seconds)

    while time.monotonic() < end_time:
        remaining = end_time - time.monotonic()
        time.sleep(min(1.0, remaining))


def serial_port_exists(port):
    """
    Prüft, ob der konfigurierte Gerätepfad existiert.

    Unterstützt sowohl /dev/ttyUSB0 als auch symbolische Links unter
    /dev/serial/by-id/.
    """
    return Path(port).exists()


def log_connection_error(port, error=None):
    """
    Klassifiziert typische Fehler beim Öffnen des seriellen Ports
    und gibt eine verständliche Fehlermeldung aus.
    """
    if not serial_port_exists(port):
        logging.error(
            "Kein USB-Schnittstellenwandler gefunden oder angeschlossen."
        )
        logging.error(
            "Der konfigurierte Gerätepfad existiert nicht: %s",
            port,
        )
        logging.error(
            "Prüfe den angeschlossenen Adapter mit: "
            "ls -la /dev/serial/by-id/"
        )
        return

    if error is None:
        logging.error(
            "Der Modbus-Port konnte nicht geöffnet werden: %s",
            port,
        )
        return

    error_text = str(error).lower()

    if "permission denied" in error_text:
        logging.error(
            "Keine Berechtigung zum Öffnen des "
            "Schnittstellenwandlers: %s",
            port,
        )
        logging.error(
            "Prüfe die Benutzergruppen mit 'groups'. "
            "Der Benutzer sollte Mitglied der Gruppe 'dialout' sein."
        )

    elif (
        "device or resource busy" in error_text
        or "resource busy" in error_text
    ):
        logging.error(
            "Der Schnittstellenwandler wird bereits von einem "
            "anderen Programm verwendet: %s",
            port,
        )

    elif (
        "no such file or directory" in error_text
        or "could not open port" in error_text
    ):
        logging.error(
            "Kein USB-Schnittstellenwandler unter dem "
            "konfigurierten Gerätepfad gefunden: %s",
            port,
        )

    else:
        logging.error(
            "Der Schnittstellenwandler konnte nicht geöffnet werden "
            "| Fehlertyp: %s | Meldung: %s",
            type(error).__name__,
            error,
        )


def run():
    setup_logger()

    # Wichtig: Diese Variablen werden einmal zu Beginn definiert und
    # stehen damit in der gesamten run()-Funktion zur Verfügung.
    port = MODBUS_CONFIG["port"]
    poll_interval = float(
        MODBUS_CONFIG["poll_interval_seconds"]
    )
    reconnect_interval = float(
        MODBUS_CONFIG["reconnect_interval_seconds"]
    )

    logging.info("=" * 60)
    logging.info("Watchdog wird gestartet.")
    logging.info("Modbus RTU Port: %s", port)
    logging.info("Baudrate: %s", MODBUS_CONFIG["baudrate"])
    logging.info("Parität: %s", MODBUS_CONFIG["parity"])
    logging.info("Slave-ID: %s", MODBUS_CONFIG["slave_id"])
    logging.info(
        "Abfrageintervall: %s Sekunden",
        poll_interval,
    )
    logging.info(
        "Wiederverbindungsintervall: %s Sekunden",
        reconnect_interval,
    )
    logging.info("=" * 60)

    database = WatchdogDatabase()
    modbus_client = None

    try:
        database.connect()
        logging.info("Datenbank erfolgreich geöffnet.")

        # Äußere Schleife:
        # Verbindung herstellen, bei Fehler warten und erneut versuchen.
        while True:
            try:
                logging.info(
                    "Versuche, den Schnittstellenwandler zu öffnen: %s",
                    port,
                )

                # Vorherigen Client sicher schließen.
                if modbus_client is not None:
                    modbus_client.close()

                # Für jeden Verbindungsversuch einen neuen Client erzeugen.
                modbus_client = WatchdogModbusClient()

                if not serial_port_exists(port):
                    raise FileNotFoundError(
                        f"Serieller Gerätepfad nicht vorhanden: {port}"
                    )

                connection_successful = modbus_client.connect()

                if not connection_successful:
                    raise ConnectionError(
                        f"Modbus-Port konnte nicht geöffnet werden: {port}"
                    )

                logging.info(
                    "Schnittstellenwandler erfolgreich geöffnet."
                )
                logging.info(
                    "Teste die Kommunikation mit dem Modbus-Regler."
                )

                first_successful_read = True

                # Innere Schleife:
                # Solange die Kommunikation läuft, zyklisch lesen.
                while True:
                    values = modbus_client.read_all_registers()

                    if first_successful_read:
                        logging.info(
                            "Modbus-Kommunikation erfolgreich. "
                            "Der Regler antwortet."
                        )
                        first_successful_read = False

                    database.insert_measurements(
                        measurements=values,
                        source=port,
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
                # Strg+C nicht als Kommunikationsfehler behandeln.
                raise

            except Exception as error:
                log_connection_error(
                    port=port,
                    error=error,
                )

                if modbus_client is not None:
                    modbus_client.close()

                logging.warning(
                    "Watchdog bleibt aktiv."
                )
                logging.warning(
                    "Nächster Verbindungsversuch in %s Sekunden.",
                    reconnect_interval,
                )

                wait_interruptible(reconnect_interval)

                logging.info(
                    "Wiederverbindungsintervall abgelaufen."
                )
                logging.info(
                    "Starte einen neuen Verbindungsversuch."
                )

    except KeyboardInterrupt:
        logging.info(
            "Watchdog wurde durch den Benutzer beendet."
        )

    except Exception as error:
        logging.critical(
            "Nicht behebbarer Programmfehler | "
            "Typ: %s | Meldung: %s",
            type(error).__name__,
            error,
        )

    finally:
        if modbus_client is not None:
            modbus_client.close()

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
