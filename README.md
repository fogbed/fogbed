Fogbed
============

### Fogbed: Containernet and Maxinet merge that allows to use Virtual Instances for resource provisioning emulation

This emulator allows the user to use Docker containers as hosts and create
Virtual Instances where the resources can be limited or overprovisioned (like a cloud). 
Two modes of emulation are available: local or distributed, enabling the construction from simple testbeds to
large ones, with many nodes. 

All the integrations are done extending functionalities from Containernet and Maxinet.

For details about how to use it, check the docs: https://fogbed.readthedocs.io

Based on: Mininet 2.3.0

* Containernet website: https://containernet.github.io/
* Mininet website:  http://mininet.org
* Original Mininet repository: https://github.com/mininet/mininet

### Features

* Add, remove Docker containers to Mininet topologies
* Connect Docker containers to topology (to switches, other containers, or legacy Mininet hosts)
* Execute commands inside Docker containers by using the Mininet CLI 
* Dynamic topology changes 
   * Add Hosts/Docker containers to a *running* Mininet topology
   * Connect Hosts/Docker containers to a *running* Mininet topology
   * Remove Hosts/Docker containers/Links from a *running* Mininet topology
* Resource limitation of Docker containers
   * CPU limitation with Docker CPU share option
   * CPU limitation with Docker CFS period/quota options
   * Memory/swap limitation
   * Change CPU/mem limitations at runtime!
* Traffic control links (delay, bw, loss, jitter)
   * (missing: TCLink support for dynamically added containers/hosts)
* Distributed emulation
* Virtual Instances to emulate multiple containers running inside a single unit with
its own resource model

### Installation
Fogbed comes with two installation and deployment options.

#### Option 1: Bare-metal installation
Automatic installation is provided through an Ansible playbook.
* Requires: Ubuntu **16.04 LTS** or newer

```bash
sudo apt-get install ansible git aptitude
git clone https://github.com/fogbed/fogbed.git
cd fogbed/ansible
sudo ansible-playbook -i "localhost," -c local install_metis.yml
sudo ansible-playbook -i "localhost," -c local install_docker.yml
sudo ansible-playbook -i "localhost," -c local --skip-tags "notindocker" install_fogbed.yml
```
Wait...

#### Option 2: Nested Docker deployment
Fogbed can be executed within a privileged Docker container (nested container deployment). 
<!---
There is also a pre-build Docker image available on [DockerHub](https://hub.docker.com/r/fogbed/fogbed/).
-->

```bash
# build the container locally
docker build -t fogbed .
```

```bash
# or pull the latest pre-build container
docker pull fogbed/fogbed
```

```bash
# run the container
docker run --name fogbed -it --rm --privileged --pid='host' -v /var/run/docker.sock:/var/run/docker.sock fogbed /bin/bash
```

### Usage / Run
Start example topology with some empty Docker containers connected to the network.

* `cd fogbed`
* run: `sudo python examples/virtual_instance_example.py`
* check the output

### Topology example

In your custom topology script you can add Docker hosts as follows:

```python

info('*** Adding docker containers\n')
topo = FogTopo()
d1 = topo.addDocker('d1', ip='10.0.0.251', dimage="ubuntu:trusty")
d2 = topo.addDocker('d2', ip='10.0.0.252', dimage="ubuntu:trusty")
d3 = topo.addHost('d3', ip='11.0.0.253', cls=Docker, dimage="ubuntu:trusty")
d4 = topo.addDocker('d4', dimage="ubuntu:trusty", volumes=["/:/mnt/vol1:rw"])

```


### Contact

#### Lead developer:
Heitor Rodrigues
* Mail: heitor1994.hr@gmail.com
* GitHub: [@heitorgo1](https://github.com/heitorgo1)

<!---
REF:

docker container run -it --rm --privileged --pid='host' --name fogbed --hostname fogbed -v /var/run/docker.sock:/var/run/docker.sock -v /home/user/myfog:/fogbed -v /home/user/myfog/share/MaxiNet-cfg-sample:/etc/MaxiNet.cfg fogbed /bin/bash
-->
