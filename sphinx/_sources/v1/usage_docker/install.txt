.. _install_docker:

Install a makina-states docker environement
============================================

Intro and history
------------------------------
Cluster based on LXC/kvm and mastersalt-pillar was the first thing we had,
This allowed us to have a git/push/deploy to environment workflow.
It's not what you ll have to use to spawn a kubernetes based cluster, as we want
things to be a lot more immutable.

We still reuse bits from the past, but we ll input the settings differently as
it was a bit too hard from end users to use that.

Idea is to deploy pre-backed containers onto production and do not do heavy configuration at runtime.
In other words, we just edit some configuration file to wire the container to server the app request, but we do not
reconfigure it from end to end.

Basic development installation
-------------------------------
Install docker
++++++++++++++++
- If you system is not supported, you can try to run it, but it just untested. you need at least docker, with aufs support.
- If you do not run ubuntu, run it intro your virtualisation software (Virtualbox, parallell, etc)
- For ubuntu, you best bet is to use **something >= Ubuntu 14.04** with a **recent kernel extras image**
  (**>=3.19** from enablement stack).
  Verify with

  .. code-block:: bash

          uname -ar

- At this time of writing, you can upgrade your kernel by issuing the following command

  .. code-block:: bash

          apt-get install linux-image-extra-3.19.0-33-generic # vivid / trusty

- Install lxc-utils & docker by reading your distribution guidelines for that purpose

    - Eg on ubuntu:

      .. code-block:: bash

            apt-get install lxc docker rsync

- Replace docker by makina-corpus version (1.9+),
  We have modified it to allow to use a custom apparmor profile instead of inject it's own and broken one.

    - The sources are `here@github <https://github.com/makinacorpus/docker.git>`_.
    - We provide a `prebuilt binary for linux <https://github.com/makinacorpus/docker/releases/download/mc_2/docker>`_.:

      .. code-block:: bash

            cp /usr/bin/docker /usr/bin/docker.dist
            curl -L --insecure -s \
                https://github.com/makinacorpus/docker/releases/download/mc_1/docker \
                -o /usr/bin/docker
            # or wget \
            #  https://github.com/makinacorpus/docker/releases/download/mc_1/docker \
            #  -O /usr/bin/docker
            chmod +x /usr/bin/docker

- If you are on Ubuntu or any system protected by **apparmor**, you ll have to tweak your apparmor installation.
  If you are not configuring your system via makina-states, you can however bring back the profile quite easily

Configure apparmor
+++++++++++++++++++++

.. code-block:: bash

    mkdir -pv /etc/apparmor.d/abstractions/lxc
    curl -L --insecure -s https://raw.githubusercontent.com/makinacorpus/makina-states/master/files/etc/apparmor.d/abstractions/lxc/powercontainer-base -o /etc/apparmor.d/abstractions/lxc/powercontainer-base
    curl -L --insecure -s https://raw.githubusercontent.com/makinacorpus/makina-states/master/files/etc/apparmor.d/abstractions/dockercontainer -o /etc/apparmor.d/abstractions/dockercontainer
    cd /tmp
    curl -L --insecure -s https://raw.githubusercontent.com/makinacorpus/makina-states/master/files/etc/apparmor.d/usr.sbin.ntpd.patch -o usr.sbin.ntpd.patch
    curl -L --insecure -s https://raw.githubusercontent.com/makinacorpus/makina-states/master/files/etc/apparmor.d/usr.sbin.ntpd.perms.patch  -o usr.sbin.ntpd.perms.patch

    cd /
    patch -Np2 < /tmp/usr.sbin.ntpd.patch
    patch -Np2 < /tmp/usr.sbin.ntpd.perms.patch
    service apparmor restart


Install the base image
++++++++++++++++++++++++++++
Clone makina-states, even if not installing it on you host

.. code-block:: bash

    mkdir /srv/mastersalt && cd /srv/mastersalt
    git clone http://github.com/makinacorpus/makina-states.git

Create the base makinacorpus/makina-states image

.. code-block:: bash

    cd /srv/mastersalt/makina-states
    ./docker/build-scratch.sh
    # at the end of the script, this will output the base image tag



