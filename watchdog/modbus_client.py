# watchdog/modbus_client.py

from pymodbus.client import ModbusSerialClient
from watchdog.config import MODBUS_CONFIG
from watchdog.register_map import REGISTER_MAP


class WatchdogModbusClient:
    def __init__(self):
        self.client = ModbusSerialClient(
            port=MODBUS_CONFIG["port"],
            baudrate=MODBUS_CONFIG["baudrate"],
            parity=MODBUS_CONFIG["parity"],
            stopbits=MODBUS_CONFIG["stopbits"],
            bytesize=MODBUS_CONFIG["bytesize"],
            timeout=MODBUS_CONFIG["timeout"],
        )

        self.slave_id = MODBUS_CONFIG["slave_id"]

    def connect(self):
        return self.client.connect()

    def close(self):
        self.client.close()

    def read_register(self, name, definition):
        register_type = definition["type"]
        address = definition["address"]
        count = definition["count"]
        scale = definition["scale"]

        if register_type == "holding":
            response = self.client.read_holding_registers(
                address=address,
                count=count,
                slave=self.slave_id,
            )
        elif register_type == "input":
            response = self.client.read_input_registers(
                address=address,
                count=count,
                slave=self.slave_id,
            )
        else:
            raise ValueError(f"Unbekannter Registertyp: {register_type}")

        if response.isError():
            raise RuntimeError(f"Fehler beim Lesen von {name}: {response}")

        raw_value = response.registers[0]
        scaled_value = raw_value * scale

        return {
            "name": name,
            "raw_value": raw_value,
            "value": scaled_value,
            "unit": definition["unit"],
            "description": definition["description"],
        }

    def read_all_registers(self):
        values = {}

        for name, definition in REGISTER_MAP.items():
            values[name] = self.read_register(name, definition)

        return values
