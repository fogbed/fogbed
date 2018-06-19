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
    software-properties-common \
    ansible \
    curl \
    iptables \
    iputils-ping \
    sudo

# install fogbed (using its Ansible playbook)
COPY . /fogbed
WORKDIR /fogbed/ansible
RUN ansible-playbook -i "localhost," -c local install_metis.yml
RUN ansible-playbook -i "localhost," -c local --skip-tags "notindocker" install.yml
WORKDIR /fogbed
RUN python setup.py develop

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

