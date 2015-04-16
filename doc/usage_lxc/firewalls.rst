
.. _lxc_firewall:

Network firewalling and masquerating a makina-states LXC based image
=====================================================================

This part is optionnal, and is relevant only if you use a firewall.

To ensure internet connectivity, you ll have to ``masquerade`` the 10.5/16
network to ensure the big internet dialog.

Although if you created the system-D or  upstart job and it does that for you, if you use an aditionnal firewall, you ll have also to double the configuration in it.

For this, you have plenty of options depending of what firewalling software you
are using.

The big picture
+++++++++++++++++
The network which will have at the end will look like::

  88.86.85.96   88.5.5.5
  NET  ---------ROUTER-------- YourHOST --- LXCBR1 (10.5.0.1)
                10.6.1.25      10.6.1.1            |
                                                   |--- LXC1 (10.5.0.6)
                                                   |
                                                   |--- LXC2 (10.5.0.7)
                                                   |
                                                   |--- LXC3 (10.5.0.8)

The 10.6/16 network is your home or work network, which can be anything like 192.168.x.x or other **rfc1918** network.

- The first thing will be to allow the traffic to jump from **lxcbr1**
  to the segment in **10.6/0**. This is done by enabling the kernel
  ip forwarding option, see :ref:`activate_forwarding`.
- The second thing will be to remap the traffic from **10.5** from coming
  from your internal machine, this is what we call **IPV4 NAT**.
  We do this with the **masquerading** stuff.
- And the third thing will be to **allow** the firewall to let pass the **lxc traffic**.

Step2 and Step3 are often done with your firewall software.

.. _install_lxc_shorewall:

shorewall
++++++++++
- Ensure to apply :ref:`activate_forwarding`.

You ll have to allow ip forwarding in ``/etc/shorewall/shorewall.conf``::

    IP_FORWARDING=Yes

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

You may want to continue with:

    - :ref:`lxc_upstart_install_firewalling`
    - :ref:`lxc_systemd_install_firewalling`
 

.. _install_lxc_firewalld:

firewalld
++++++++++
- Ensure to apply :ref:`activate_forwarding`.

Identify and allow lxc traffic
--------------------------------
::

    firewall-cmd --add-zone=lxc --permanent
    firewall-cmd --permanent --zone=lxc --add-interface=lxcbr1
    firewall-cmd --permanent --zone=lxc --set-target=ACCEPT

Masquerade public ip
---------------------
Masquerade whatever what are your public zones with one or more of the following commands::

    firewall-cmd --permanent --zone=home --add-masquerade
    firewall-cmd --permanent --zone=external --add-masquerade
    firewall-cmd --permanent --zone=public --add-masquerade

You may want to continue with:

    - :ref:`lxc_upstart_install_firewalling`
    - :ref:`lxc_systemd_install_firewalling`
 
.. _install_lxc_ufw:

ufw
+++

- Ensure to apply :ref:`activate_forwarding`.
- create or edit ``/etc/default/ufw`` and add/update **DEFAULT_FORWARD_POLICY**

::

  DEFAULT_FORWARD_POLICY="ACCEPT"

- Create or edit ``/etc/ufw/before.rules``
  and add or adapt

::

    *nat
    :POSTROUTING ACCEPT [0:0]
    -A POSTROUTING -s 10.5/16 -o eth0 -j MASQUERADE
    # don't delete the 'COMMIT' line or these nat table rules won't be processed
    COMMIT


- You will have to add here any network you are bridging from the lxcbr1 bridge (and by default we use 10.5/16).

You may want to continue with:

    - :ref:`lxc_upstart_install_firewalling`
    - :ref:`lxc_systemd_install_firewalling`
 

.. _install_lxc_iptables:

iptables
+++++++++
This means that you manage your firewall manually, you are on your own baby, just allow the traffic from and to lxcbr1 (10.5/16) and masquerade it.

You may want to continue with:

    - :ref:`lxc_upstart_install_firewalling`
    - :ref:`lxc_systemd_install_firewalling`


