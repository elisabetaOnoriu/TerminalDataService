import logging
import sys
from cgitb import handler


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s:     %(name)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
