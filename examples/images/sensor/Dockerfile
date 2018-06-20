FROM python:2

RUN apt-get update && apt-get install -y \
    net-tools \
    iputils-ping \
    iproute \
    && apt-get clean \
    && rm -rf /var/tmp/*

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x ./start.sh

ENV FLASK_APP main.py
ENV FLASK_PORT 3000

EXPOSE 3000

ENTRYPOINT ./start.sh