
.. _create_lxc_container:

Create a container
===============================
Briefing
---------------
As soon as you have the base template or any template derived from it,
you can spawn a new container based on those template.

The filesystem from this base container will be copied, and all
further modifications will only exist on your new container.

There are some steps involved in cloning a makina-states based container:

    - clone the LXC container
    - reset the lxc bare informations like the mac, and the ip
    - reset the SSH and salt information inside the new container
    - maybe mark the salt installations (salt & mastersalt) as masterless

For this we created a simple helper freeing you from this hassle.

Spawn the container
---------------------

You can use it the following way::

    cd makina-states
    sudo ./_scripts/spawn_container.py --name=<name> [ ... optional opts ]

Examples::

    # get random non allocated it
    sudo ./_scripts/spawn_container.py --name=<name>
    sudo ./_scripts/spawn_container.py --ip=<new_ip in 10.5 range> --name=<name>

The name of the container will become it's **minion_id**.

A good idea is to name containers with a FQDN like::

    sudo ./_scripts/spawn_container.py [--mac=xx:xx:xx:xx:xx:xx] [--ip=10.5.0.3] --name=myproject.lxc.local

The ip and mac will be generated from non allocated ports, if they are not
specified, you can then edit the LXC config to get them::

    vim /var/lib/lxc/<container_name>/config

They are the value of:

    - ``lxc.network.ipv4``
    - ``lxc.network.hwaddr``

- You may use sudo to allow automaticly the sudoer user ssh keys to connect into
  the container via ssh

Network configuration
----------------------
To access services on your container, you may want to edit your **HOST**
``/etc/hosts`` and add those types of redirections::

    10.5.0.3 myproject.lxc.local www.foo.com

Where:

    - **10.5.0.3** is the ip of your container
    - **myproject.lxc.local** and **www.foo.com** would be domains that you want
      to access inside your lxc.

Think that any entry in your **/etc/hosts** will shadow any real DNS
information, and that can be harmful if you use real DNS informations like
**www.google.com**, just remember if you shadows a real name, that your
LXC will be used in place of the real internet service.

SSH connection
---------------------
All the keys from your host root's ssh folder and user folder if the container
was spawned using sudo are allowed to connect as **root** via ssh on the
container.

Connect to your container these ways:

    - ssh rooŧ@10.5.0.3
    - ssh root@@myproject.lxc.local (if you added something in your ``/etc/hosts``

Edit files of the container from your host
-----------------------------------------------
You can use **sshfs** to easily edit the files inside your container from your
host.

Just issue::

    mkdir myhost
    sshfs rooŧ@10.5.0.3:/ myhost

This will mount the **/** of your container in myhost, and you ll can edit the
files as if you were directly on the host.
Don't forget that you are connected as root user, and files created will be
owned by root and respect UMASK and acls settings from your container.


To umount::

    fusermount -u myhost

If your shell seems blocked::

    killall -9 sshfs
    fusermount -u myhost

if the fusermount failed::

    sudo umount -f /home/user/myhost

Conclusion
-----------
You may now want to continue with

    - :ref:`install_lxc_ubuntu_conclusion`
    - :ref:`install_lxc_systemd_conclusion`

