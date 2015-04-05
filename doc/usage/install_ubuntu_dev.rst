Install lxc
--------------
Official doc: https://help.ubuntu.com/lts/serverguide/lxc.html

First install LXC
::

 sudo apt-get install lxc


Prepare network connectivity
-------------------------------
In makina-states, our images are known to use a network bridge called
``lxcbr1``.

They use the ``10.5/16`` network and ``10.5.0.1`` as the default gateway.

For this to work, you have plenty of solutions.


Network bridge
~~~~~~~~~~~~~~~
The first thing you ll have to do is to persist the network bridge.
For this, on ubuntu, the simpliest thing is to inspire ourselves from the
default lxc-net configuration and create the following configuration file


Networg route forwarding
~~~~~~~~~~~~~~~~~~~~~~~~~~


Network firewalling and masquerating
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
To ensure internet connectivity, you ll have to ``masquerade`` the 10.5/16
network to ensure the big internet dialog.
For this, you have plenty of options depending of what firewalling software you
are using.

shorewall
++++++++++

ufw
+++

iptables
+++++++++


Install the base LXC container
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Download and install the lxc container is simplified through a python script.
You can do that by issuing as root the follwing commands::

    git clone https://github.com/makinacorpus/makina-states.git
    ./_scripts/restore_lxc_image.py



