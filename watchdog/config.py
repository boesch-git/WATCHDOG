# watchdog/config.py

#This is a temporary config file, later there will be probably an external watchdog.yaml or something. 

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

APP_CONFIG = {
    "log_file": "logs/watchdog.log",
}