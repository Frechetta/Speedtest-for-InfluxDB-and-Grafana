FROM python:3.9-slim-buster
MAINTAINER Eric Frechette <frechetta93@gmail.com>

RUN apt update && \
    apt install -y tini

WORKDIR /app/

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY config.ini .
COPY influxspeedtest/ influxspeedtest/

USER 1000:1000

ENTRYPOINT ["tini", "--", "python", "-m", "influxspeedtest.main"]
