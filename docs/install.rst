
Installation
============

Fogbed comes with two installation and deployment options.

Bare-metal installation
-----------------------

Automatic installation is provided through an Ansible playbook.

* Requires: at least Ubuntu **16.04 LTS**

.. code-block:: console

    $ sudo apt-get install ansible git aptitude
    $ git clone https://github.com/fogbed/fogbed.git
    $ cd fogbed/ansible
    $ sudo ansible-playbook -i "localhost," -c local install_metis.yml
    $ sudo ansible-playbook -i "localhost," -c local install_docker.yml
    $ sudo ansible-playbook -i "localhost," -c local --skip-tags "notindocker" install.yml

Nested Docker deployment
------------------------

Fogbed can be executed within a privileged Docker container
(nested container deployment).
There is also a pre-build Docker image available on `DockerHub`_.

.. code-block:: console

    # build the container locally
    $ docker build -t fogbed .

    # or pull the latest pre-built container
    $ docker pull fogbed/fogbed

.. code-block:: console

    # run the container
    $ docker run --name fogbed -it --rm --privileged --pid='host' -v /var/run/docker.sock:/var/run/docker.sock fogbed /bin/bash


Good luck!

..  For an automatic installation of MaxiNet use the installer.sh script.
    You can download it here: [installer.sh]
    Just copy the script to each physical machine you want to use MaxiNet on and execute the script as the user you later on want to run MaxiNet with. Note that the username has to be the same across all installations.
    If you are running Ubuntu, you now have to setup your user to use sudo without password. This can simply be done by adding the following line to your /etc/sudoers file.
    yourusername ALL=(ALL) NOPASSWD: ALL
    Replace yourusername with your user name.
    The last thing left to do is copy the MaxiNet.cfg to /etc/ and modify it accordingly.
    sudo cp ~/MaxiNet/share/MaxiNet-cfg-sample /etc/MaxiNet.cfg
    If you do not wish to have the MaxiNet.cfg in /etc/ you can also save it to ~/.MaxiNet.cfg
    Edit the config file according to the hints given at our wiki.
    Note that under Ubuntu, you need to set
    [all]
    ...
    sshuser = yourusername
    usesudo = True

.. toctree::
    :maxdepth: 4

.. _DockerHub: https://hub.docker.com/r/fogbed/fogbed/
