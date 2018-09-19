FROM ubuntu:xenial

# install required packages
RUN apt-get clean
RUN apt-get update \
    && apt-get install -y  git \
    net-tools \
    aptitude \
    build-essential \
    python-setuptools \
    python-dev \
    python-pip \
    python-matplotlib \
    software-properties-common \
    ansible \
    curl \
    iptables \
    iputils-ping \
    sudo \
    cmake \
    sysstat \
    uuid-runtime \
    ca-certificates \
    autoconf \
    apt-transport-https \
    nano \
    && apt-get clean \
    && rm -rf /var/tmp/*


# install fogbed (using its Ansible playbook)
COPY . /fogbed
WORKDIR /fogbed

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /fogbed/ansible
RUN ansible-playbook -i "localhost," -c local install_metis.yml
RUN ansible-playbook -i "localhost," -c local install_docker.yml
RUN ansible-playbook -i "localhost," -c local --skip-tags "notindocker" install_fogbed.yml
WORKDIR /fogbed
RUN python setup.py develop

RUN chmod a+x src/maxinet/Scripts/*

# tell containernet that it runs in a container
ENV CONTAINERNET_NESTED 1

# namespace port
EXPOSE 9090

# sshd port
EXPOSE 5345

# Controller port
EXPOSE 6633

# Important: This entrypoint is required to start the OVS service
ENTRYPOINT ["util/docker/entrypoint.sh"]
CMD ["python", "examples/containernet_example.py"]

