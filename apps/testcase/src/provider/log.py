import logging
from rich.logging import RichHandler

# Configura o log para usar Rich
logging.basicConfig(
    level=logging.DEBUG,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler()]
)

logger = logging.getLogger("development")

class RichStdOutputProtocol:
    def __init__(self, *prefix):
        self.prefix = prefix
    def write(self, message: str):
        logger.info(f"[SHELL] [{".".join(self.prefix)}] {message}")