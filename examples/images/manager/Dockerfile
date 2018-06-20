FROM python:2

RUN apt-get update && apt-get install -y \
    net-tools \
    iputils-ping \
    iproute

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x ./start.sh

ENV FLASK_APP main.py
ENV FLASK_PORT 2000

EXPOSE 2000

#CMD [ "python", "./your-daemon-or-script.py" ]
ENTRYPOINT ./start.sh