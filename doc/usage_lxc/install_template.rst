
.. _install_lxc_template:

Install the base LXC container
===============================
First ensure that there is plenty of space on ``/var/lib/lxc``.
Plently as at least **10GB**.

If you do not have enought place on the partition, you may have another mounted
partition or one that you can create which will provide that extra space.
Follow the next chapter to add this extra space.

On other cases, you can directly jump to :ref:`install_lxc_template_image`.

Make room for space (optional)
--------------------------------

Mount your origin partition
++++++++++++++++++++++++++++++++
When you have this partition, first ensure that it is mounted, and it has a
relevant entry on your ``/etc/fstab`` for it to be mounted at boot time.

For example, Imagine that you have mounted your data partition in ``/home``,
you will have to have or to add  one like which looks like one on those following entries in your ``/etc/fstab`` file::

    # Origin target fstype fsopts * *
    UUID=19710386-5ed2-4b6c-b289-628adac75e5b /home ext4 defaults 0 0
    # those lines are equivalent
    # /dev/sdc4                               /home ext4 default 0 0

If you want to use ``UUIDS``, you can find the uuid belonging to one partition like
this::

    ls /dev/disk/by-uuid/

Of course, **xfs** and **ext4** can be any supported filesystem except fat or
ntfs.

The options **defaults** can be different on your installation, this is probably not a problem.

The filesystem can by encrypted, it will obisouly be slowier but it will work.

Map your original partition to ``/var/lib/lxc``
++++++++++++++++++++++++++++++++++++++++++++++++
Then, you ll have to map this extra big partition to ``/var/lib/lxc``.
Wwe will use that as a ``bind mound`` (a powerfull symlink like
redirection).

We will call ``/home``, this extra big partition mountpoint.

Remapping a directory from this partition is as simple as:

    - Creating the directory on your partition holding the new mountpoint::

        mkdir -p /home/var/lib/lxc

    - adding a new entry at the bottom of your fstab::

        /home/var/lib/lxc /var/lib/lxc none bind,defaults,exec 0 0

You will obviously replace ``/home`` by the mountpoint location of your extra big data partititon.
You will obviously replace ``/home/var/lib/lxc`` by the directory you had created previously.

You can then activate this configuration it with::

    mount /var/lib/lxc

And verify the extra space on it with::

    df -f /var/lib/lxc

Which should be the same that::

    df -h /home/var/lib/lxc

As it is now on your fstab, it will survive to reboots.

- That means that  ``/home/var/lib/lxc`` is mounted in place of ``/var/lib/lxc``
- Anything which is written to or accessed from ``/var/lib/lxc``
  will instead be written in ``/home/var/lib/lxc``.

.. _install_lxc_template_image:

Install base LXC Image
--------------------------------
Download and install the lxc container is simplified through a python script.

Download a copy of makina-states, which contains helpers::

    git clone https://github.com/makinacorpus/makina-states.git -b stable

You can do that by issuing as root those following commands::

    cd makina-states
    git checkout stable
    # either sudo, or use a root shell
    sudo ./_scripts/restore_lxc_image.py

This will download and install your image in ``/var/lib/lxc``.

Finish installation
------------------------
If you were following the general installation procedure for the LXC procedure, you may go back to the general docuementation by following one of those following links:

    - :ref:`lxc_upstart_install_firewalling`
    - :ref:`lxc_systemd_install_firewalling`
