# watchdog/logger.py
#
# Copyright (c) 2026 G. Aue, N. Diedrich. Licensed under the MIT License.
#


import logging
from pathlib import Path

from watchdog.config import APP_CONFIG


def setup_logger():
    log_file = Path(APP_CONFIG["log_file"])
    log_file.parent.mkdir(exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return


    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)  

#    logging.basicConfig(
 #       filename=log_dir / "watchdog.log",
  #      level=logging.INFO,
   #     format="%(asctime)s | %(levelname)s | %(message)s",
    #)
#
 #   console = logging.StreamHandler()
  #  console.setLevel(logging.INFO)
   # formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    #console.setFormatter(formatter)
#
# #   logging.getLogger("").addHandler(console)
#