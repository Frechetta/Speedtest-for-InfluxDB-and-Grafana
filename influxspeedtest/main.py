import logging
import sys
import time
from typing import Optional
import argparse
from requests.exceptions import ConnectTimeout, ConnectionError
import speedtest
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError, InfluxDBServerError
from influxspeedtest.utils import config

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="A tool to take network speed test and send the results to InfluxDB")
    parser.parse_args(sys.argv[1:])
    collector = InfluxdbSpeedtest()
    collector.run()


class InfluxdbSpeedtest:
    def __init__(self):
        self.influx_client = self._get_influx_connection()

    @staticmethod
    def _get_influx_connection() -> InfluxDBClient:
        """
        Create an InfluxDB connection and test to make sure it works.
        We test with the get all users command.  If the address is bad it fails
        with a 404.  If the user doesn't have permission it fails with 401
        :return:
        """
        client = InfluxDBClient(
            host=config.influx_address,
            port=config.influx_port,
            database=config.influx_database,
            ssl=config.influx_ssl,
            verify_ssl=config.influx_verify_ssl,
            username=config.influx_user,
            password=config.influx_password,
            timeout=5
        )

        try:
            logger.debug('Testing connection to InfluxDB using provided credentials')
            client.get_list_database()  # TODO - Find better way to test connection and permissions
            logger.debug('Successful connection to InfluxDB')
        except (ConnectTimeout, InfluxDBClientError, ConnectionError) as e:
            if isinstance(e, ConnectTimeout):
                logger.critical('Unable to connect to InfluxDB at the provided address (%s)', config.influx_address)
            elif e.code == 401:
                logger.critical('Unable to connect to InfluxDB with provided credentials')
            else:
                logger.critical('Failed to connect to InfluxDB for unknown reason')

            sys.exit(1)

        return client

    def run(self):
        while True:
            if not config.servers:
                self.run_speed_test()
            else:
                for server in config.servers:
                    self.run_speed_test(server)

            logger.info('Waiting %s seconds until next test', config.delay)
            time.sleep(config.delay)

    def run_speed_test(self, server: Optional[str] = None):
        """
        Performs the speed test with the provided server
        :param server: Server to test against
        """
        server_str = server if server is not None else 'auto'
        logger.info(f'Starting speed test for server "{server_str}"')

        speedtest.build_user_agent()

        try:
            tester = speedtest.Speedtest()
        except speedtest.ConfigRetrievalError:
            logger.critical('Failed to get speedtest.net configuration. Aborting')
            sys.exit(1)

        try:
            self.setup_speedtest(tester, server)
        except speedtest.NoMatchedServers:
            logger.error('No matched servers: %s', server)
            return
        except speedtest.ServersRetrievalError:
            logger.critical('Cannot retrieve speedtest.net server list. Aborting')
            return
        except speedtest.InvalidServerIDType:
            logger.error('%s is an invalid server type, must be int', server)
            return

        logger.debug('Starting download test')
        tester.download()
        logger.debug('Starting upload test')
        tester.upload()

        results = tester.results.dict()
        self.send_results(results)

        logger.info('Download: %sMbps - Upload: %sMbps - Latency: %sms',
                    round(results['download'] / 1000000, 2),
                    round(results['upload'] / 1000000, 2),
                    results['server']['latency'])

    @staticmethod
    def setup_speedtest(tester: speedtest.Speedtest, server: Optional[str] = None):
        """
        Initializes the Speed Test client with the provided server
        :param tester: SpeedTest object
        :param server: server list
        :return: None
        """
        logger.debug('Setting up speedtest.net client')

        if server is None:
            servers = []
        else:
            servers = server.split() # Single server to list

        tester.get_servers(servers)

        logger.debug('Picking the closest server')
        tester.get_best_server()

        logger.info(f'Selected server {tester.best["id"]} in {tester.best["name"]}')

    def send_results(self, results_dict):
        """
        Formats the payload to send to InfluxDB
        :rtype: None
        """
        input_points = [
            {
                'measurement': 'speed_test_results',
                'fields': {
                    'download': results_dict['download'],
                    'upload': results_dict['upload'],
                    'ping': results_dict['server']['latency'],
                    'server': results_dict['server']['id'],
                    'server_name': results_dict['server']['name']
                },
                'tags': {
                    'server': results_dict['server']['id'],
                    'server_name': results_dict['server']['name'],
                    'server_country': results_dict['server']['country']
                }
            }
        ]

        self.write_influx_data(input_points)

    def write_influx_data(self, json_data):
        """
        Writes the provided JSON to the database
        :param json_data:
        :return: None
        """
        logger.debug(f'Sending to InfluxDB: {json_data}')

        def write():
            try:
                self.influx_client.write_points(json_data)
            except Exception as e:
                if type(e) in [InfluxDBClientError, ConnectionError, InfluxDBServerError] \
                        and hasattr(e, 'code') and e.code == 404:
                    raise DbDoesNotExistError()
                logger.error('Failed to write to InfluxDB')
                logger.exception(e)
            else:
                logger.info('Data written to InfluxDB')

        try:
            write()
        except DbDoesNotExistError:
            logger.error(f'Database {config.influx_database} does not exist. Attempting to create and retry')
            self.influx_client.create_database(config.influx_database)
            write()


class DbDoesNotExistError(Exception):
    pass


if __name__ == '__main__':
    main()
