import sys
import logging
from influxspeedtest.config import config


class SingleLevelFilter(logging.Filter):
    def __init__(self, passlevel, above=True):
        super().__init__()
        self.passlevel = passlevel
        self.above = above

    def filter(self, record):
        if self.above:
            return record.levelno >= self.passlevel
        else:
            return record.levelno <= self.passlevel


root_logger = logging.getLogger('root')
root_logger.setLevel(config.logging_level)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

general_handler = logging.StreamHandler(sys.stdout)
general_filter = SingleLevelFilter(logging.INFO, False)
general_handler.setFormatter(formatter)
general_handler.addFilter(general_filter)
root_logger.addHandler(general_handler)

error_handler = logging.StreamHandler(sys.stderr)
error_filter = SingleLevelFilter(logging.WARNING)
error_handler.setFormatter(formatter)
error_handler.addFilter(error_filter)
root_logger.addHandler(error_handler)

root_logger.propagate = False