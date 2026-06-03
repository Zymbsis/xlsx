import logging
import sys
from typing import Literal


def setup_logging(environment: Literal["dev", "prod"]) -> None:
    level = logging.DEBUG if environment == "dev" else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )
