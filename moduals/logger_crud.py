import logging
import os

class LoggingManager:
    def __init__(self, log_file: str = "logfile.log", level: int = logging.DEBUG):
        self.logger = logging.getLogger("SystemLogger")
        self.logger.setLevel(level)
        self.logger.propagate = False

        if not self.logger.handlers:
            # Console Handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)
            console_handler.setFormatter(logging.Formatter(
                "[%(asctime)s] [%(levelname)s] %(message)s", "%H:%M:%S"
            ))

            # File Handler
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_handler.setFormatter(logging.Formatter(
                "[%(asctime)s] [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S"
            ))

            self.logger.addHandler(console_handler)
            self.logger.addHandler(file_handler)

    def get_logger(self):
        return self.logger
