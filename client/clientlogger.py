import logging
import logging.handlers
from config.client_config import Config
import os

if not os.path.exists(Config.log_dir):
    os.makedirs(Config.log_dir)

client_logger = logging.getLogger(__name__)
client_logger.setLevel(level = logging.DEBUG)
log_path = Config.log_dir + "/client.log"
handler = logging.handlers.TimedRotatingFileHandler(log_path, 'D', 1, 0)
handler.suffix = '%Y%m%d'
formatter = logging.Formatter('%(asctime)s %(levelname)s - %(message)s')
handler.setFormatter(formatter)
client_logger.addHandler(handler)


stat_logger = logging.getLogger("STAT")
stat_logger.setLevel(level = logging.DEBUG)
log_path = Config.log_dir + "/stat.log"
handler = logging.handlers.TimedRotatingFileHandler(log_path, 'D', 1, 0)
handler.suffix = '%Y%m%d'
formatter = logging.Formatter('%(asctime)s %(levelname)s - %(message)s')
handler.setFormatter(formatter)
stat_logger.addHandler(handler)