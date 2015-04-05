.. _lxc_firewall:

Network firewalling and masquerating a makina-states LXC based image
=====================================================================
This part is optionnal, and is relevant only if you use a firewall.

To ensure internet connectivity, you ll have to ``masquerade`` the 10.5/16
network to ensure the big internet dialog.

Although if you created the system-D or  upstart job and it does that for you, if you use an aditionnal firewall, you ll have also to double the configuration in it.

For this, you have plenty of options depending of what firewalling software you
are using.


.. _install_lxc_shorewall:

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

.. _install_lxc_firewalld:

firewalld
++++++++++++

.. _install_lxc_ufw:

ufw
+++

.. _install_lxc_iptables

iptables
+++++++++
This means that you manage your firewall manually, you are on your own baby, just allow the traffic from and to lxcbr1 (10.5/16) and masquerade it.
