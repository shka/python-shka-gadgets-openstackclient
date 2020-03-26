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

``sshfs`` and ``curl`` are prerequisites, and this plugin can be installed
from PyPI using pip. It will install also a minimal OSC
(=python-openstackclient) for the "vanilla" server management.

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

    openstack vanilla create --flavor standard.tiny --key-name mykey --image Ubuntu-18.04 --login ubuntu test

It creates a vanilla server named ``test`` on ``standard.tiny`` flavor from
the Ubuntu 18.04 image. The specified key pair must be registered
already. It gives a floating IP address to the vanilla and prepares a
security group to login via ssh. And, in this case, the home directory
of user ``ubuntu`` is accessible from ``./vanilla`` via sshfs.

.. code:: shell

    openstack server ssh --login ubuntu test

You can login to ``test`` as avobe if the login name is ``ubuntu``.

.. code:: shell

    openstack vanilla shelve test

It shelves ``test`` - It's good when you will leave the project
temporarily. The floating IP address and the security group is taken
away. The old image used for the previous unshelve is removed. The
``./vanilla`` folder would be unmounted.

.. code:: shell

    openstack vanilla unshelve --login ubuntu test

You can unshelve ``test`` when you restart the project. The floating IP
address and the security group are configured again. The ``./vanilla``
folder would be mounted again.

.. code:: shell

    openstack vanilla resize --flavor standard.xxlarge test

You can resize ``test`` when you need more power, if the project supports it.

.. code:: shell

    openstack vanilla delete test

After the project you can remove ``test`` completely.

There are more subcommands and the options of each subcommand. ``--help``
option will show them. For example,

.. code:: shell

    $ openstack vanilla --help
    Command "vanilla" matches:
      vanilla allow me
      vanilla create
      vanilla delete
      vanilla deny us
      vanilla give ip
      vanilla mount
      vanilla resize
      vanilla shelve
      vanilla show id
      vanilla show ip
      vanilla show my ip
      vanilla show status
      vanilla take ip
      vanilla unmount
      vanilla unshelve
      vanilla wait sshd
    $ openstack vanilla create --help
    usage: openstack vanilla create [-h] [--add-port <port>] --flavor <flavor>
    				--login <login-name> [--mount <mount-point>]
    				--key-name <key-name> --image <image>
    				[--volume <volume>]
    				<server>

    Create a vanilla server.

    positional arguments:
      <server>              Server (name or ID)

    optional arguments:
      -h, --help            show this help message and exit
      --add-port <port>     Destination port (allow multiple times, default: [22])
      --flavor <flavor>     Create with this flavor (name or ID)
      --login <login-name>  Login name for sshfs mount (ssh -l option)
      --mount <mount-point>
    			Directory of the vanilla server to mount (default: ~)
      --key-name <key-name>
    			Keypair to inject into this server (optional
    			extension)
      --image <image>       Create server boot disk from this image (name or ID)
      --volume <volume>     Volume (size in GB for new or ID to mount)

    This command is provided by the python-shka-gadgets-openstackclient plugin.
    $

Copyright
---------

See ./LICENSE
