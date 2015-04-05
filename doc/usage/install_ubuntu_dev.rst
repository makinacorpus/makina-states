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

First, create this upstart job ``/etc/init/lxc-net-makina.conf``:

    description "lxc makina network"
    author "Mathieu Le Marec - Pasquet <kiorky@cryptelium.net>"

    start on starting lxc
    stop on stopped lxc

    env USE_LXC_BRIDGE="True"
    env LXC_MAKINA_BRIDGE="lxcbr1"
    env LXC_MAKINA_ADDR="10.5.0.1"
    env LXC_MAKINA_NETMASK="255.255.0.0"
    env LXC_MAKINA_NETWORK="10.5.0.0/16"
    env varrun="/var/run/lxc"
    env LXC_DOMAIN=""
    env LXC_MAKINA_DOMAIN=""

    pre-start script
            [ -f /etc/default/lxc ] && . /etc/default/lxc

            [ "x$USE_LXC_BRIDGE" = "xtrue" ] || { stop; exit 0; }

            cleanup() {
                    # dnsmasq failed to start, clean up the bridge
                    iptables -t nat -D POSTROUTING -s ${LXC_MAKINA_NETWORK} ! -d ${LXC_MAKINA_NETWORK} -j MASQUERADE || true
                    ifconfig ${LXC_MAKINA_BRIDGE} down || true
                    brctl delbr ${LXC_MAKINA_BRIDGE} || true
            }

            if [ -d /sys/class/net/${LXC_MAKINA_BRIDGE} ]; then
                    if [ ! -f ${varrun}/network_up ]; then
                            # bridge exists, but we didn't start it
                            stop;
                    fi
                    exit 0;
            fi

            # set up the lxc network
            brctl addbr ${LXC_MAKINA_BRIDGE} || { echo "Missing bridge support in kernel"; stop; exit 0; }
            echo 1 > /proc/sys/net/ipv4/ip_forward
            mkdir -p ${varrun}
            ifconfig ${LXC_MAKINA_BRIDGE} ${LXC_MAKINA_ADDR} netmask ${LXC_MAKINA_NETMASK} up
            iptables -t nat -A POSTROUTING -s ${LXC_MAKINA_NETWORK} ! -d ${LXC_MAKINA_NETWORK} -j MASQUERADE

            LXC_MAKINA_DOMAIN_ARG=""
            if [ -n "$LXC_MAKINA_DOMAIN" ]; then
                    LXC_MAKINA_DOMAIN_ARG="-s $LXC_MAKINA_DOMAIN"
            fi
            touch ${varrun}/network_up
    end script

    post-stop script
            [ -f /etc/default/lxc ] && . /etc/default/lxc
            [ -f "${varrun}/network_up" ] || exit 0;
            # if $LXC_MAKINA_BRIDGE has attached interfaces, don't shut it down
            ls /sys/class/net/${LXC_MAKINA_BRIDGE}/brif/* > /dev/null 2>&1 && exit 0;

            if [ -d /sys/class/net/${LXC_MAKINA_BRIDGE} ]; then
                    ifconfig ${LXC_MAKINA_BRIDGE} down
                    iptables -t nat -D POSTROUTING -s ${LXC_MAKINA_NETWORK} ! -d ${LXC_MAKINA_NETWORK} -j MASQUERADE || true
                    brctl delbr ${LXC_MAKINA_BRIDGE}
            fi
            rm -f ${varrun}/network_up
    end script


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


Network firewalling and masquerating
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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


Install the base LXC container
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Download and install the lxc container is simplified through a python script.
You can do that by issuing as root the follwing commands::

    git clone https://github.com/makinacorpus/makina-states.git
    ./_scripts/restore_lxc_image.py

This will download and install your image in ``/var/lib/lxc``.
