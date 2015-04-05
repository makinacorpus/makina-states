.. _install_lxc_template:

Install the base LXC container
===============================
Make room for space
--------------------------
First ensure that there is plenty of space on ``/var/lib/lxc``


Download and install the lxc container is simplified through a python script.
You can do that by issuing as root the follwing commands::

    git clone https://github.com/makinacorpus/makina-states.git
    ./_scripts/restore_lxc_image.py

This will download and install your image in ``/var/lib/lxc``.

Note about firewalling
------------------------
Last but not least,  if you use a firewall, and we hope you do so, please refer to the firewalling section for further configuration.

Please read :ref:`lxc_firewall`.
