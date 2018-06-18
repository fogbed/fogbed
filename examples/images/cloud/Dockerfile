FROM python:2

RUN apt-get update && apt-get install -y \
    net-tools \
    iputils-ping \
    iproute

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP main.py

#CMD [ "python", "./your-daemon-or-script.py" ]
CMD /bin/bash