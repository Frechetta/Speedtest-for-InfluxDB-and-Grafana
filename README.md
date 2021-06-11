**Speedtest.net Collector For InfluxDB and Grafana**
------------------------------

![Screenshot](https://puu.sh/tmfOA/b5576e88de.png)

This tool is a wrapper for speedtest-cli which allows you to run periodic speed tests and send the results to InfluxDB.

## Configuration within config.ini

Sample config file (with defaults):

    # config.ini

    [general]
    delay = 300                 # delay between runs in seconds
    
    [influxdb]
    address = influxdb          # address of InfluxDB (IP or hostname)
    port = 8086                 # port that InfluxDB is running on; (8086 in most cases)
    database = speedtests       # database to write speed test stats to
    username =                  # user with access to database
    password =                  # password for user
    influx_ssl = False          # whether to use SSL or not
    influx_verify_ssl = True    # if using SSL, whether to verify the SSL connection or not 
    
    [speedtest]
    server =                    # comma-seperated list of servers; leave blank for auto
    
    [logging]
    level = debug               # log level; valid options: debug, info, warning, error, critical

## Usage

### Docker

1. Create a config file
1. Modify the config file with your influxdb settings
1. Run the container, using a bind-mount for the config file
    1. Using `docker run`
     
        ```bash
        docker run -d --name speedtest -v $(pwd)/config.ini:/app/config.ini frechetta93/speedtest-for-influxdb-and-grafana
        ```
    1. Using `docker-compose`
    
        Create the `docker-compose.yml` file:
     
        ```yaml
        version: '3'

        services:
            speedtest:
                image: frechetta93/speedtest-for-influxdb-and-grafana
                container_name: speedtest
                volumes:
                  - ./config.ini:/app/config.ini
        ```
        
        Run:

        ```bash
        docker-compose up -d
        ```

### No Docker

1. Enter your desired information in config.ini
1. `pip3 install -r requirements.txt`
1. `python3 -m influxspeedtest.main`

#### Requirements

Python 3.7+

#### Custom Config File Name

If you wish to use a config file with a different name, set an environment variable called INFLUXSPEEDTESTCONFIG with
the config file path.
