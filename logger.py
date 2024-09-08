import logging
from logging.handlers import TimedRotatingFileHandler
import os

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

if not os.path.exists('./log'):
    os.mkdir('./log')

file_handler = TimedRotatingFileHandler('./log/sdapi.log', when='D', interval=1)
file_handler.suffix = '%Y-%m-%d.log'
file_handler.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)