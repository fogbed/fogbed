
Getting Started
===============


Getting started text

.. note::

   This function is not suitable for sending spam e-mails.

.. deprecated:: 3.1
   Use :func:`spam` instead.

.. seealso::

   Module :py:mod:`zipfile`
      Documentation of the :py:mod:`zipfile` standard module.

   `GNU tar manual, Basic Tar Format <http://link>`_
      Documentation for tar archive files, including GNU tar extensions.

.. hlist::
   :columns: 3

   * A list of
   * short items
   * that should be
   * displayed
   * horizontally

.. glossary::

   environment
      A structure where information about all documents under the root is
      saved, and used for cross-referencing.  The environment is pickled
      after the parsing stage, so that successive runs only need to read
      and parse new and changed documents.

   source directory
      The directory which, including its subdirectories, contains all
      source files for one Sphinx project

.. sectionauthor:: Guido van Rossum <guido@python.org>

.. index::
   single: execution; context
   module: __main__
   module: sys
   triple: module; search; path

.. math::

   (a + b)^2 = a^2 + 2ab + b^2

   (a - b)^2 = a^2 - 2ab + b^2

.. math::
   :nowrap:

   \begin{eqnarray}
      y    & = & ax^2 + bx + c \\
      f(x) & = & x^2 + 2xy + y^2
   \end{eqnarray}

.. productionlist::
   try_stmt: try1_stmt | try2_stmt
   try1_stmt: "try" ":" `suite`
            : ("except" [`expression` ["," `target`]] ":" `suite`)+
            : ["else" ":" `suite`]
            : ["finally" ":" `suite`]
   try2_stmt: "try" ":" `suite`
            : "finally" ":" `suite`


+------------------------+------------+----------+----------+
| Header row, column 1   | Header 2   | Header 3 | Header 4 |
| (header rows optional) |            |          |          |
+========================+============+==========+==========+
| body row 1, column 1   | column 2   | column 3 | column 4 |
+------------------------+------------+----------+----------+
| body row 2             | ...        | ...      |          |
+------------------------+------------+----------+----------+

There are two ways to get started using MaxiNet: Using our preconfigured Virtual Machine Images or installing from scratch.
For starters, we recommend to use our preconfigured Virtual Machine Images. When performance matters, MaxiNet should definitively be used on non-virtualized machines.

Download these two Virtual Machine images:
[MaxiNet-1.0-rc1.ova] MD5 (MaxiNet-1.0-rc1.ova) = 6dfc4546bd48bc727861b0ad51ecf2ca

The username for both machines is maxinet with the password maxinet.

The file MaxiNet-1.0-rc1.ova contains two virtual machine images: worker1 and worker 2.
You need a program like Virtual Box to run them on your computer.

Start each virtual machine on a dedicated physical machine and make sure the virtual machines can reach each other. For testing purposes both virtual machines can also run on the same physical machine.
The virtual machines are using the IP addresses 192.168.0.1 and 192.168.0.2 on the interface eth0. Make sure both machines can reach each other.
To start the emulation process, login into worker1 and cd to /home/maxinet/maxinet/Frontend/examples/
Specify the OpenFlow controller by editing the file /etc/MaxiNet.cfg. You have to change the line
controller = "192.168.0.1:6633" # default controller
to point to the IP address of your OpenFlow controller. Make sure the controller is reachable from both worker1 and worker2.
You can also start a pox controller at worker1 by invoking the commands:

.. code-block:: console

    maxinet@worker1:~$ cd pox
    maxinet@worker1:~/pox$ screen -d -m -S PoxScr ./pox.py forwarding.l2_learning

Before any MaxiNet expepriment can be executed, you first need to start the MaxiNetFrontendServer and the MaxiNetWorkerServers. To this end, on worker1, execute the following commands to start both the Frontend and a Worker:

.. code-block:: console

    maxinet@worker1:~$ screen -d -m -S MaxiNetFrontend MaxiNetFrontendServer
    maxinet@worker1:~$ screen -d -m -S MaxiNetWorker sudo MaxiNetWorker

and on worker2, execute the following to start a second Worker:

.. code-block:: console

    maxinet@worker2:~$ sudo screen -d -m -S MaxiNetWorker MaxiNetWorker

Until now, we have a running Frontend server with two connected Workers. You can check the status of the MaxiNet cluster with the command MaxiNetStatus

.. code-block:: console

    maxinet@worker2:~$ MaxiNetStatus
    MaxiNet Frontend server running at 192.168.0.1
    Number of connected workers: 2
    --------------------------------
    worker1		free
    worker2		free

As you can see, the cluster has two workers which are currently not allocated to an experiment.

You can now start the simplePing example as user maxinet.

.. code-block:: console

    maxinet@worker1:~/maxinet/Frontend/examples$ python simplePing.py

You can find even more examples under ~/maxinet/Frontend/examples.

.. toctree::
    :maxdepth: 4

