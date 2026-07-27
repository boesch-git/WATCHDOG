# watchdog/config.py

MODBUS_CONFIG = {
    "port": "/dev/ttyUSB0",
    "baudrate": 9600,
    "bytesize": 8,
    "parity": "N",
    "stopbits": 1,
    "timeout": 2,
    "slave_id": 1,
    "poll_interval_seconds": 5,
}
