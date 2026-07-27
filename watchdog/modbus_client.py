# watchdog/modbus_client.py

import inspect

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

    def _call_with_slave_id(self, method, address, count):
        parameters = inspect.signature(method).parameters

        if "slave" in parameters:
            return method(
                address=address,
                count=count,
                slave=self.slave_id,
            )

        if "unit" in parameters:
            return method(
                address=address,
                count=count,
                unit=self.slave_id,
            )

        if "device_id" in parameters:
            return method(
                address=address,
                count=count,
                device_id=self.slave_id,
            )

        return method(
            address,
            count,
        )

    def _read_holding_registers(self, address, count):
        return self._call_with_slave_id(
            self.client.read_holding_registers,
            address,
            count,
        )

    def _read_input_registers(self, address, count):
        return self._call_with_slave_id(
            self.client.read_input_registers,
            address,
            count,
        )

    def read_register(self, name, definition):
        register_type = definition["type"]
        address = definition["address"]
        count = definition["count"]
        scale = definition.get("scale", 1.0)

        if register_type == "holding":
            response = self._read_holding_registers(address, count)
        elif register_type == "input":
            response = self._read_input_registers(address, count)
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
            "unit": definition.get("unit", ""),
            "description": definition.get("description", name),
            "address": address,
            "type": register_type,
        }

    def read_all_registers(self):
        values = {}

        for name, definition in REGISTER_MAP.items():
            values[name] = self.read_register(name, definition)

        return values
