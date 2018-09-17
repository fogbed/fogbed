
Introduction
============

Fogbed is a framework that extends the `Mininet`_ emulator to create fog testbeds in
virtualized environments. Using a desktop approach, Fogbed enables the deployment of virtual
fog nodes as Docker containers under different network conﬁgurations.
The Fogbed API provides functionality to add, connect and remove containers dynamically
from the network topology. These features allow for the emulation of real world
cloud and fog infrastructures in which it is possible to start and stop compute instances at
any point in time. Also, it is possible to change at runtime resource limitations for a
container, such as CPU time and memory available.

A Fogbed emulation environment can be created by deploying virtual nodes, virtual
switches, virtual connections and virtual instances in a virtual network environment
running on a host machine. The ﬂexible setup is achieved by using preconﬁgured Docker
container images. Each container image comprises part of a distributed application,
required services and protocols. Different types of container images can be used to
instantiate virtual nodes.

The virtual instance is an abstraction that allows for the management of a
related set of virtual nodes and virtual switches as a single entity.
A fog application and its services run in one or more virtual nodes inside a virtual instance.
Virtual instances differ by the type of resource model applied to them, it could be an over
provisioning model, where the resource allocation mimics a cloud, or a limiting model,
where the resource allocation is restricted to mimic low cost edge devices.
The management system process is responsible for deploying and starting the instances in the
Fogbed emulation environment. It ﬁrst executes a script that deﬁnes the network topology
between virtual instances. The communication between a virtual instance and the management
system is performed through a well-deﬁned instance API.


.. _Mininet: http://mininet.org/