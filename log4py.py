import logging
from colorlog import ColoredFormatter
import os
from typing import Type


class LoggerManager:
    _log_format = "%(log_color)s%(asctime)s - %(levelname)s - %(message)s"
    _formatter = ColoredFormatter(
        _log_format,
        log_colors={
            "DEBUG": "white",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        },
    )

    _handler = logging.StreamHandler()
    _handler.setFormatter(_formatter)

    @classmethod
    def get_logger(cls, name: str) -> Type[logging.Logger]:
        if not os.path.exists('logs'):
            os.makedirs('logs')

        log_file = f'logs/{name}.log'

        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

        logger = logging.getLogger(name)
        if not logger.handlers:
            logger.setLevel(logging.DEBUG)
            logger.addHandler(cls._handler)
            logger.addHandler(file_handler)
        return logger


__all__ = ["LoggerManager"]
