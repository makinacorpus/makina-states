.. _activate_forwarding:

Network route forwarding
-------------------------
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

You may want to continue with:

    - :ref:`lxc_upstart_install_image`
    - :ref:`lxc_systemd_install_image`
