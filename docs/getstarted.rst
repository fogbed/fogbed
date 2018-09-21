Getting Started
===============

After having installed fogbed in a VM or in the Docker container, you can start
using it running an example topology:

.. code-block:: console

    # inside the VM or container with fogbed installed
    $ python examples/virtual_instance_example.py

If everything was done right until now, it will instantiate a few hosts and ping one another.

Local emulation
---------------

Checking the content of the example we have:

.. code-block:: python

    import time

    from src.fogbed.experiment import FogbedExperiment, FogbedDistributedExperiment
    from src.fogbed.resourcemodel import CloudResourceModel, EdgeResourceModel, FogResourceModel, PREDEFINED_RESOURCES
    from src.fogbed.topo import FogTopo
    from src.mininet.link import TCLink
    from src.mininet.log import setLogLevel
    from src.mininet.node import OVSSwitch

    setLogLevel('info')

    topo = FogTopo()

    c1 = topo.addVirtualInstance("cloud")
    f1 = topo.addVirtualInstance("fog")
    e1 = topo.addVirtualInstance("edge")

    erm = EdgeResourceModel(max_cu=20, max_mu=2048)
    frm = FogResourceModel()
    crm = CloudResourceModel()

    e1.assignResourceModel(erm)
    f1.assignResourceModel(frm)
    c1.assignResourceModel(crm)

    d1 = c1.addDocker('d1', ip='10.0.0.251', dimage="ubuntu:trusty")
    d2 = f1.addDocker('d2', ip='10.0.0.252', dimage="ubuntu:trusty")
    d3 = e1.addDocker('d3', ip='10.0.0.253', dimage="ubuntu:trusty")
    d4 = topo.addDocker('d4', ip='10.0.0.254', dimage="ubuntu:trusty")
    d5 = e1.addDocker('d5', ip='10.0.0.255', dimage="ubuntu:trusty", resources=PREDEFINED_RESOURCES['medium'])
    d6 = e1.addDocker('d6', ip='10.0.0.256', dimage="ubuntu:trusty", resources=PREDEFINED_RESOURCES['large'])

    s1 = topo.addSwitch('s1')
    s2 = topo.addSwitch('s2')

    topo.addLink(d4, s1)
    topo.addLink(s1, s2)
    topo.addLink(s2, e1)
    topo.addLink(c1, f1, cls=TCLink, delay='200ms', bw=1)
    topo.addLink(f1, e1, cls=TCLink, delay='350ms', bw=2)

    exp = FogbedExperiment(topo, switch=OVSSwitch)
    exp.start()

    try:
        print exp.get_node("cloud.d1").cmd("ifconfig")
        print exp.get_node(d2).cmd("ifconfig")

        print "waiting 5 seconds for routing algorithms on the controller to converge"
        time.sleep(5)

        print exp.get_node(d1).cmd("ping -c 5 10.0.0.252")
        print exp.get_node("fog.d2").cmd("ping -c 5 10.0.0.251")
    finally:
        exp.stop()

As can be seen, a fogbed topology definition is a python script where all the
hosts and links are described, and at the end a predefined experiment can be run
on top of it.

First, let's look closely at the first part:

.. code-block:: python

    topo = FogTopo()

    c1 = topo.addVirtualInstance("cloud")
    f1 = topo.addVirtualInstance("fog")
    e1 = topo.addVirtualInstance("edge")

    erm = EdgeResourceModel(max_cu=20, max_mu=2048)
    frm = FogResourceModel()
    crm = CloudResourceModel()

    e1.assignResourceModel(erm)
    f1.assignResourceModel(frm)
    c1.assignResourceModel(crm)

Here we have the instantiation of a fog topology, used by fogbed, followed by the
definition of 3 Virtual Instances.
A Virtual Instance in the context of fogbed is a unit that can have one or more
hosts linked together by a single switch. Each Virtual Instance has a resource model
associated with it that defines how many resources that instance have so that they can be
distributed among it's containers.

The resource model use is based on the proposed in `son-emu`_, each resource model
has a ``max_cu`` and ``max_mu`` value, representing the maximum computing and memory units
the Virtual Instance that assigns it has.

Then, each container determines how much ``cu`` and ``mu`` they have, representing how many
parts of the total of it's Virtual Instance is available to the container. These values
are converted to real cpu time and memory limit.

Example: if a container ``a`` is assigned 4 computing units and container ``b`` 2 computing units,
and they are both in the same Virtual Instance, container ``a`` has twice more cpu time than
container ``b``.

There are three types of resource models in fogbed right now: ``EdgeResourceModel``,
``FogResourceModel`` and ``CloudResourceModel`` and the default ``max_cu`` and ``max_mu`` values
are 32 and 2048, respectively. Currently, Fog and Cloud resource models
are the same, using an over-provisioning strategy where if a container requests resources
and all of it was already allocated to other containers, the new container starts anyway
and the cpu time and memory limit for every container is recalculated.
The Edge resource model has a fixed limit strategy, where if a container requests resources
and all of it was already allocated, an exception is raised alerting that it can't allocate
anymore resources for new containers.

Second code block:

.. code-block:: python

    d1 = c1.addDocker('d1', ip='10.0.0.251', dimage="ubuntu:trusty")
    d2 = f1.addDocker('d2', ip='10.0.0.252', dimage="ubuntu:trusty")
    d3 = e1.addDocker('d3', ip='10.0.0.253', dimage="ubuntu:trusty")
    d4 = topo.addDocker('d4', ip='10.0.0.254', dimage="ubuntu:trusty")
    d5 = e1.addDocker('d5', ip='10.0.0.255', dimage="ubuntu:trusty", resources=PREDEFINED_RESOURCES['medium'])
    d6 = e1.addDocker('d6', ip='10.0.0.256', dimage="ubuntu:trusty", resources=PREDEFINED_RESOURCES['large'])

    s1 = topo.addSwitch('s1')
    s2 = topo.addSwitch('s2')

    topo.addLink(d4, s1)
    topo.addLink(s1, s2)
    topo.addLink(s2, e1)
    topo.addLink(c1, f1, cls=TCLink, delay='200ms', bw=1)
    topo.addLink(f1, e1, cls=TCLink, delay='350ms', bw=2)

It is similar to examples from `Containernet`_ and other emulators based
on `Mininet`_. Here each new host is started with some information
about it, every one, except ``d4``, is started inside a Virtual Instance. The ``resources``
field in ``d5`` and ``d6`` describe how much of the Virtual Instance resources that container should take.
If it isn't specified, the predefined resource named *small* is chosen. Below is the list of the predefined
resources table:

.. code-block:: python

    PREDEFINED_RESOURCES = {
        "tiny": {"cu": 0.5, "mu": 32},
        "small": {"cu": 1, "mu": 128},
        "medium": {"cu": 4, "mu": 256},
        "large": {"cu": 8, "mu": 512},
        "xlarge": {"cu": 16, "mu": 1024},
        "xxlarge": {"cu": 32, "mu": 2048}
    }

If none of the predefined resources is suitable for your application, you can pass a custom one.

After the creation of all hosts, two switches are instantiated followed by the connections
between stray hosts, Virtual Instances and switches.

Third code block:

.. code-block:: python

    exp = FogbedExperiment(topo, switch=OVSSwitch)
    exp.start()

    try:
        print exp.get_node("cloud.d1").cmd("ifconfig")
        print exp.get_node(d2).cmd("ifconfig")

        print "waiting 5 seconds for routing algorithms on the controller to converge"
        time.sleep(5)

        print exp.get_node(d1).cmd("ping -c 5 10.0.0.252")
        print exp.get_node("fog.d2").cmd("ping -c 5 10.0.0.251")
    finally:
        exp.stop()

Here an experiment is created for the newly made topology. After it's start,
we tell the steps it should follow. In this example we are checking the command ``ifconfig``
inside the host ``d1`` that is inside the Virtual Instance ``cloud``, and then running the
same command inside host ``d2``, this time using a variable reference instead of passing a name string.
After 5 seconds waiting, it runs a ping from ``d1`` to ``d2``, and vice-versa.

Distributed emulation
---------------------

The previous example explored a single host emulation, but fogbed can be adapted using
an interface, like the one provided by `Maxinet`_, to execute the topology distributed in many machines.

First, make sure that all the machines that are going to run fogbed distributed have it installed
and that they can reach each other.

Start the SDN controller ``pox`` in one of the machines, it should've been installed
alongside fogbed:

.. code-block:: console

    # you can find the pox folder in the same directory you put fogbed
    # in case you are running fogbed inside Docker, pox path is /pox
    $ cd pox
    $ ./pox.py forwarding.l2_learning

Copy the content from ``/usr/local/share/maxinet/config.example`` to ``/etc/MaxiNet.cfg``,
it should look more or less like this:

::

    [all]
    password = HalloWelt
    controller = 172.17.0.2:6633
    logLevel = INFO        ; Either CRITICAL, ERROR, WARNING, INFO  or DEBUG
    port_ns = 9090         ; Nameserver port
    port_sshd = 5345       ; Port where MaxiNet will start an ssh server on each worker
    runWith1500MTU = False ; Set this to True if your physical network can not handle MTUs >1500.
    useMultipleIPs = 0     ; for RSS load balancing. Set to n > 0 to use multiple IP addresses per worker. More information on this feature can be found at MaxiNets github Wiki.
    deactivateTSO = True   ; Deactivate TCP-Segmentation-Offloading at the emulated hosts.
    sshuser = root         ; On Debian set this to root. On ubuntu set this to user which can do passwordless sudo
    usesudo = False        ; If sshuser is set to something different than root set this to True.
    useSTT = False         ; enables stt usage for tunnels. Only usable with OpenVSwitch. Bandwithlimitations etc do not work on STT tunnels!

    [FrontendServer]
    ip = 172.17.0.2
    threadpool = 256       ; increase if more workers are needed (each Worker requires 2 threads on the FrontendServer)

    [worker1-hostname]
    ip = 172.17.0.2
    share = 1

    [worker2-hostname]
    ip = 172.17.0.3
    share = 1


Substitute the field ``controller`` with the address of the machine running ``pox``.

In the ``ip`` field of the FrontendServer put the address of the machine you intend to run the FrontendServer.

For each worker in you network, put it's hostname and ip address at the lines below the FrontendServer,
like the example.

To check the hostname and ip of a machine, just run in the terminal:

.. code-block:: console

    # print hostname
    $ hostname

    # print ip
    $ ip -4 addr show

Now, in the machine that you specified as FrontendServer, run it:

.. code-block:: console

    $ sudo FogbedFrontendServer

And for each worker, run:

.. code-block:: console

    $ sudo FogbedWorker

Check the status of the cluster with:

.. code-block:: console

    $ FogbedStatus
    MaxiNet Frontend server running at 172.17.0.2
    Number of connected workers: 2
    --------------------------------
    worker1-hostname		free
    worker2-hostname		free

If everything went well, adjust the previous example to run distributed,
you only need to change the experiment class to ``FogbedDistributedExperiment``
and save the file.

.. code-block:: python

    exp = FogbedDistributedExperiment(topo, switch=OVSSwitch)
    exp.start()

    try:
        print exp.get_node("cloud.d1").cmd("ifconfig")
        print exp.get_node(d2).cmd("ifconfig")

        print "waiting 5 seconds for routing algorithms on the controller to converge"
        time.sleep(5)

        print exp.get_node(d1).cmd("ping -c 5 10.0.0.252")
        print exp.get_node("fog.d2").cmd("ping -c 5 10.0.0.251")
    finally:
        exp.stop()

Now run the topology script in the FrontendServer machine:

.. code-block:: console

    $ python examples/virtual_instance_example.py


.. todo::

    Add more details about examples
    Add more examples

.. toctree::
    :maxdepth: 4

.. _son-emu: https://github.com/sonata-nfv/son-emu
.. _Containernet: https://github.com/containernet/containernet
.. _Mininet: https://github.com/mininet/mininet
.. _Maxinet: https://github.com/MaxiNet/MaxiNet
