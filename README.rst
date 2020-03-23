    :Author: Shintaro Katayama

.. contents::



python-shka-gadgets-openstackclient
-----------------------------------

This is a plugin of OpenStackClient (a.k.a. OSC) to make a single and
simple virtual machine handy. In a typical use-case, the virtual
machine (names "vanilla" here) given a floating IP address is created
and used interactively. Sometimes the vanilla would be shelved; the
floating IP address and the security rules are taken away when it is
shelved, and these are given again when it is unshelved. After the
interactive tasks, the given resources and the images would be cleaned
out. The "vanilla" plugin simplifies such resource management in the
project work.

Getting Started
---------------

This plugin can be installed from PyPI using pip. It will install also
a minimal OSC (=python-openstackclient) for the "vanilla" server
management.

Example
-------

.. code:: shell

    python3 -m venv venv3
    . ./venv3/bin/activate
    pip3 install python-shka-gadgets-openstackclient
    . ./openrc.sh

The ``openrc.sh`` here is a script for OSC environment, which you can
download from the OpenStack dashboard of your project. The script will
ask a password of the project.

.. code:: shell

    openstack vanilla create --flavor standard.tiny --key-name mykey --image Ubuntu-18.04 test

It creates a vanilla server named ``test`` on ``standard.tiny`` flavor from
the Ubuntu 18.04 image. The specified key pair must be registered
already. It gives a floating IP address to the vanilla and prepares a
security group to login via ssh.

.. code:: shell

    openstack server ssh --login ubuntu test

You can login to ``test`` as avobe if the login name is ``ubuntu``.

.. code:: shell

    mkdir -p ~/mnt/ubuntu
    sshfs ubuntu@`openstack vanilla show ip test`: ~/mnt/ubuntu
    ls -l ~/mnt/ubuntu
    umount ~/mnt/ubuntu

You can mount ``ubuntu``'s home directory of ``test`` by sshfs, if you prefer.

.. code:: shell

    openstack vanilla shelve test

It shelves ``test`` - It's good when you will leave the project
temporarily. The floating IP address and the security group is taken
away. The old image used for the previous unshelve is removed.

.. code:: shell

    openstack vanilla unshelve test

You can unshelve ``test`` when you restart the project. The floating IP
address and the security group are configured again.

.. code:: shell

    openstack vanilla resize --flavor standard.xxlarge test

You can resize ``test`` when you need more power, if the project supports it.

.. code:: shell

    openstack vanilla delete test

After the project you can remove ``test`` completely.

Copyright
---------

See ./LICENSE
