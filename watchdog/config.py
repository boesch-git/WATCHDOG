# watchdog/config.py
#
# Copyright (c) 2026 G. Aue, N. Diedrich. Licensed under the MIT License.
#

#This is a temporary config file, later there will be probably an external watchdog.yaml or something. 


#deprecated version:
# MODBUS_CONFIG = {
#     "port": "/dev/ttyUSB0",
#     "baudrate": 9600,
#     "bytesize": 8,
#     "parity": "N",
#     "stopbits": 1,
#     "timeout": 2,
#     "slave_id": 1,
#     "poll_interval_seconds": 5,

#     #Wartezeit nach Kommunikationsfehlern
#     "reconnect_interval_seconds": 60,
# }

# APP_CONFIG = {
#     "log_file": "logs/watchdog.log",
# }

# DATABASE_CONFIG = {
#     "path": "data/watchdog.db",
# }

# Revision with a JSON config file, located in /config/watchdog.json

import json
from pathlib import Path


import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "watchdog.json"


class ConfigurationError(Exception):
    """Fehler beim Laden oder Prüfen der Watchdog-Konfiguration."""


def resolve_project_path(path_value):
    path = Path(path_value).expanduser()

    if path.is_absolute():
        return path

    return PROJECT_ROOT / path


def load_json_file(file_path):
    file_path = Path(file_path)

    if not file_path.exists():
        raise ConfigurationError(
            f"JSON-Datei nicht gefunden: {file_path}"
        )

    try:
        with file_path.open("r", encoding="utf-8") as json_file:
            data = json.load(json_file)

    except json.JSONDecodeError as error:
        raise ConfigurationError(
            f"Ungültiges JSON in {file_path}, "
            f"Zeile {error.lineno}, Spalte {error.colno}: "
            f"{error.msg}"
        ) from error

    except OSError as error:
        raise ConfigurationError(
            f"Datei konnte nicht gelesen werden: "
            f"{file_path}: {error}"
        ) from error

    if not isinstance(data, dict):
        raise ConfigurationError(
            f"Die oberste Ebene muss ein JSON-Objekt sein: "
            f"{file_path}"
        )

    return data


def require_section(config, section_name):
    section = config.get(section_name)

    if not isinstance(section, dict):
        raise ConfigurationError(
            f"Konfigurationsabschnitt fehlt oder ist ungültig: "
            f"'{section_name}'"
        )

    return section


def require_key(section, section_name, key):
    if key not in section:
        raise ConfigurationError(
            f"Pflichtfeld fehlt: '{section_name}.{key}'"
        )

    return section[key]


def validate_main_config(config):
    application = require_section(config, "application")
    modbus = require_section(config, "modbus")
    database = require_section(config, "database")
    registers = require_section(config, "registers")

    require_key(application, "application", "log_file")
    require_key(database, "database", "path")
    require_key(registers, "registers", "path")

    required_modbus_keys = (
        "port",
        "baudrate",
        "parity",
        "stopbits",
        "bytesize",
        "timeout",
        "slave_id",
        "poll_interval_seconds",
        "reconnect_interval_seconds",
    )

    for key in required_modbus_keys:
        require_key(modbus, "modbus", key)

    try:
        modbus["port"] = str(modbus["port"])
        modbus["baudrate"] = int(modbus["baudrate"])
        modbus["parity"] = str(modbus["parity"]).upper()
        modbus["stopbits"] = int(modbus["stopbits"])
        modbus["bytesize"] = int(modbus["bytesize"])
        modbus["timeout"] = float(modbus["timeout"])
        modbus["slave_id"] = int(modbus["slave_id"])
        modbus["poll_interval_seconds"] = float(
            modbus["poll_interval_seconds"]
        )
        modbus["reconnect_interval_seconds"] = float(
            modbus["reconnect_interval_seconds"]
        )

    except (TypeError, ValueError) as error:
        raise ConfigurationError(
            f"Ungültiger Datentyp in der Modbus-Konfiguration: {error}"
        ) from error

    if modbus["parity"] not in {"N", "E", "O"}:
        raise ConfigurationError(
            "Ungültige Parität. Erlaubt sind N, E oder O."
        )

    if modbus["baudrate"] <= 0:
        raise ConfigurationError(
            "Die Baudrate muss größer als 0 sein."
        )

    if modbus["bytesize"] not in {5, 6, 7, 8}:
        raise ConfigurationError(
            "Die Anzahl der Datenbits muss 5, 6, 7 oder 8 sein."
        )

    if modbus["stopbits"] not in {1, 2}:
        raise ConfigurationError(
            "Die Anzahl der Stopbits muss 1 oder 2 sein."
        )

    if not 1 <= modbus["slave_id"] <= 247:
        raise ConfigurationError(
            "Die Modbus-Slave-ID muss zwischen 1 und 247 liegen."
        )

    if modbus["timeout"] <= 0:
        raise ConfigurationError(
            "Der Modbus-Timeout muss größer als 0 sein."
        )

    if modbus["poll_interval_seconds"] <= 0:
        raise ConfigurationError(
            "Das Abfrageintervall muss größer als 0 sein."
        )

    if modbus["reconnect_interval_seconds"] <= 0:
        raise ConfigurationError(
            "Das Wiederverbindungsintervall muss größer als 0 sein."
        )

    return config


def validate_register_map(register_map):
    if not isinstance(register_map, dict) or not register_map:
        raise ConfigurationError(
            "Die Registerliste ist leer oder ungültig."
        )

    for name, definition in register_map.items():
        if not isinstance(definition, dict):
            raise ConfigurationError(
                f"Registerdefinition '{name}' ist ungültig."
            )

        if "address" not in definition:
            raise ConfigurationError(
                f"Registeradresse fehlt bei '{name}'."
            )

        if "type" not in definition:
            raise ConfigurationError(
                f"Registertyp fehlt bei '{name}'."
            )

        try:
            definition["address"] = int(definition["address"])
            definition["count"] = int(definition.get("count", 1))
            definition["scale"] = float(
                definition.get("scale", 1.0)
            )

        except (TypeError, ValueError) as error:
            raise ConfigurationError(
                f"Ungültiger Zahlenwert bei Register "
                f"'{name}': {error}"
            ) from error

        definition["type"] = str(
            definition["type"]
        ).lower()

        definition["unit"] = str(
            definition.get("unit", "")
        )

        definition["description"] = str(
            definition.get("description", name)
        )

        if definition["type"] not in {"holding", "input"}:
            raise ConfigurationError(
                f"Ungültiger Registertyp bei '{name}': "
                f"'{definition['type']}'"
            )

        if definition["address"] < 0:
            raise ConfigurationError(
                f"Negative Registeradresse bei '{name}'."
            )

        if not 1 <= definition["count"] <= 125:
            raise ConfigurationError(
                f"Ungültige Registeranzahl bei '{name}'."
            )

    return register_map


def load_configuration(config_path=DEFAULT_CONFIG_PATH):
    config_path = Path(config_path).resolve()

    config = load_json_file(config_path)
    config = validate_main_config(config)

    register_path = resolve_project_path(
        config["registers"]["path"]
    )

    register_config = load_json_file(register_path)

    if "registers" not in register_config:
        raise ConfigurationError(
            f"Abschnitt 'registers' fehlt in: {register_path}"
        )

    register_map = validate_register_map(
        register_config["registers"]
    )

    config["application"]["log_file"] = str(
        resolve_project_path(
            config["application"]["log_file"]
        )
    )

    config["database"]["path"] = str(
        resolve_project_path(
            config["database"]["path"]
        )
    )

    config["registers"]["resolved_path"] = str(register_path)
    config["config_file"] = str(config_path)

    return config, register_map


# Konfiguration und Registerliste beim Programmstart laden
CONFIG, REGISTER_MAP = load_configuration()

APP_CONFIG = CONFIG["application"]
MODBUS_CONFIG = CONFIG["modbus"]
DATABASE_CONFIG = CONFIG["database"]