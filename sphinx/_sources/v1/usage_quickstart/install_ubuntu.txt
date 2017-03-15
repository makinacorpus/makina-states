Install LXC makina-states on ubuntu with upstart
===========================================================

Install lxc
--------------
Official doc: https://help.ubuntu.com/lts/serverguide/lxc.html

First install LXC
::

 sudo apt-get install lxc bridge-utils

Prepare network connectivity
-------------------------------
In makina-states, our images are known to use a network bridge called
``lxcbr1``.

They use the ``10.5/16`` network and ``10.5.0.1`` as the default gateway.

For this to work, you have plenty of solutions.

Network bridge
----------------
The first thing you ll have to do is to persist the network bridge.
For this, on ubuntu, the simpliest thing is to inspire ourselves from the
default lxc-net configuration and create the following configuration file

First, create **as root** this upstart job ``/etc/init/lxc-net-makina.conf`` & helpers::

    for i in /etc/init/lxc-net-makina\
             /usr/bin/magicbridge.sh /etc/reset-net-bridges;do
     curl --silent \
      "https://raw.githubusercontent.com/makinacorpus/makina-states/stable/files${i}" \
      > "${i}"
    done
    chmod 644 /etc/init/lxc-net-makina
    chmod 755 /usr/bin/magicbridge.sh /etc/reset-net-bridges
    cp /usr/bin/magicbridge.sh /usr/bin/lxc-net-makina.sh

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

Activate kernel forwarding
---------------------------
Please follow :ref:`activate_forwarding`.

.. _lxc_upstart_install_image:

Install the image on ubuntu
-------------------------------
You can now read and proceed with the following section, :ref:`install_lxc_template`.


.. _lxc_upstart_install_firewalling:

Note about firewalling on ubuntu
----------------------------------
Last but not least, if you use a firewall, and we hope you do so, please refer to the firewalling section for further configuration. Please read :ref:`lxc_firewall`.

On ubuntu you may be using:

    - :ref:`install_lxc_ufw`
    - :ref:`install_lxc_shorewall`

Install a new container
------------------------
- Refer to :ref:`create_lxc_container`

.. _install_lxc_ubuntu_conclusion:

Conclusion (ubuntu)
-----------------------
Well done, you may now enjoy your new container
You may want to continue with:

    - :ref:`projects_intro`

