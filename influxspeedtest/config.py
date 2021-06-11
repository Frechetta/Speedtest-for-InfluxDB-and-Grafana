import os
import sys
import configparser
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class Config:
    def __init__(self, file_path: Path):
        logger.debug(f'Loading configuration file {file_path}')
        
        if not file_path.is_file():
            logger.error(f'Unable to load config file: {file_path}')
            sys.exit(1)
        
        self.config = configparser.ConfigParser()
        self.config.read(file_path)

        # General
        section_general = self.config['general']
        self.delay = section_general.getint('delay', fallback=300)

        # InfluxDB
        section_influxdb = self.config['influxdb']
        self.influx_address = section_influxdb.get('address', fallback='influxdb')
        if not self.influx_address:
            logger.error('config option "influxdb.address" is required')
            sys.exit(1)
        self.influx_port = section_influxdb.getint('port', fallback=8086)
        self.influx_database = section_influxdb.get('database', fallback='speedtests')
        self.influx_user = section_influxdb.get('username', fallback='')
        self.influx_password = section_influxdb.get('password', fallback='')
        self.influx_ssl = section_influxdb.getboolean('ssl', fallback=False)
        self.influx_verify_ssl = section_influxdb.getboolean('verify_ssl', fallback=True)

        # Speedtest
        section_speedtest = self.config['speedtest']
        server_str = section_speedtest.get('server', fallback='')

        # Logging
        section_logging = self.config['logging']
        self.logging_level = section_logging.get('level', fallback='debug').upper()

        self.servers = []
        if server_str:
            self.servers = server_str.split(',')
        
        logger.debug('Configuration successfully loaded')


cfg_path = Path(os.environ.get('INFLUXSPEEDTESTCONFIG', 'config.ini'))
config = Config(cfg_path)
