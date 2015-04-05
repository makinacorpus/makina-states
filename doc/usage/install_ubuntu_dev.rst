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

First, create **as root** this upstart job ``/etc/init/lxc-net-makina.conf``::

    curl --silent https://raw.githubusercontent.com/makinacorpus/makina-states/stable/files/gen/etc/init/lxc-net-makina.conf >> /etc/init/lxc-net-makina.conf
    chmod 644 lxc-net-makina.conf

Don't forget that you can read the upstart job but basically, it creates the bridge and then masquerade the outband traffic.

Then reload it with::

    service lxc-net-makina restart

You will see you newly created bridge with::

    # ip addr show dev lxcbr1
    5: lxcbr1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default
        link/ether fe:16:a7:12:b3:3e brd ff:ff:ff:ff:ff:ff
        inet 10.5.0.1/16 brd 10.5.255.255 scope global lxcbr1
           valid_lft forever preferred_lft forever
        inet6 fe80::c9f:baff:fe43:a2ef/64 scope link
           valid_lft forever preferred_lft forever
    # ifconfig lxcbr1
    lxcbr1    Link encap:Ethernet  HWaddr fe:16:a7:12:b3:3e
              inet adr:10.5.0.1  Bcast:10.5.255.255  Masque:255.255.0.0
              adr inet6: fe80::c9f:baff:fe43:a2ef/64 Scope:Lien
              UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1
              Packets reçus:2567376 erreurs:0 :0 overruns:0 frame:0
              TX packets:5204695 errors:0 dropped:0 overruns:0 carrier:0
              collisions:0 lg file transmission:0
              Octets reçus:135360650 (135.3 MB) Octets transmis:1160735414 (1.1 GB)


Network route forwarding
~~~~~~~~~~~~~~~~~~~~~~~~~~
There is a 'systctl' option controlling weither a datagram can be sent or not
(http://en.wikipedia.org/wiki/IP_forwarding).
You have to enable it for LXC to work.
Another thing will be to make it persist to further reboots.

Create ``/etc/sysctl.d/99_custom.conf``
::

    net.ipv4.ip_forward = 1

And reload it with::

    sysctl --system

Then ensure that it is enabled with::

    sysctl net.ipv4.ip_forward


A note on  network firewalling and masquerating (optional)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This part is optionnal, and is relevant only if you use a firewall.

To ensure internet connectivity, you ll have to ``masquerade`` the 10.5/16
network to ensure the big internet dialog.
Although the upstart job does that for you, if you use an aditionnal firewall, you ll have also to double the configuration in it.
For this, you have plenty of options depending of what firewalling software you
are using.

shorewall
++++++++++
You ll have to add a ``masq`` in ``/etc/shorewall/masq``::

    br0 lxcbr1  -   -   -   -   -

Replace br0 with your primary interface like ``eth0`` or ``em1``?

You ll have to create a **lxc** zone in ``/etc/shorewall/zones``::

    lxc ipv4  -   -   -

You ll have then to attach lxcbr1 to a **lxc** zone in ``/etc/shorewall/interfaces``::

    lxc lxcbr1  routeback,bridge,tcpflags,nosmurfs

Then, you ll mark this lxc zone as trusted in ``/etc/shorewall/policy``,
Make sure that the lxc rules are prior to any blocking rules.::

    lxc net ACCEPT  -   -
    $FW lxc ACCEPT  -   -

Then reload shorewall::

    shorewall safe-restart

ufw
+++

iptables
+++++++++
This means that you manage your firewall manually, you are on your own baby, just allow the traffic from and to lxcbr1 (10.5/16) and masquerade it.

Install the base LXC container
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Download and install the lxc container is simplified through a python script.
You can do that by issuing as root the follwing commands::

    git clone https://github.com/makinacorpus/makina-states.git
    ./_scripts/restore_lxc_image.py

This will download and install your image in ``/var/lib/lxc``.
