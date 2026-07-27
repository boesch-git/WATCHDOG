# watchdog/register_map.py

REGISTER_MAP = {
    "user_outlet_temperature": {
        "address": 0,
        "count": 1,
        "type": "holding",
        "scale": 0.1,
        "unit": "°C",
        "description": "Vorlauftemperatur",
    },
    "user_outlet_temperature": {
        "address": 1,
        "count": 1,
        "type": "holding",
        "scale": 0.1,
        "unit": "°C",
        "description": "Rücklauftemperatur",
    },
    "outdoor_temperature": {
        "address": 2,
        "count": 1,
        "type": "holding",
        "scale": 0.1,
        "unit": "°C",
        "description": "Außentemperatur",
    },
    "compressor_speed": {
        "address": 10,
        "count": 1,
        "type": "holding",
        "scale": 1,
        "unit": "rpm",
        "description": "Verdichterdrehzahl",
    },
}
