# watchdog/logger.py

import logging
from pathlib import Path


def setup_logger():
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        filename=log_dir / "watchdog.log",
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    console.setFormatter(formatter)

    logging.getLogger("").addHandler(console)
