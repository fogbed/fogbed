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
ENV FLASK_PORT 4000

EXPOSE 4000

CMD [ "./start.sh"]
#CMD /bin/bash