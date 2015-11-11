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
- For ubuntu, you best bet is to use something >= Ubuntu 14.04 with a recent kernel (from enablement stack)
- Install docker by reading your distribution guidelines for that purpose

    - Eg on ubuntu:

      .. code-block:: bash

            apt-get install lxc docker rsync

    - Replace docker by makina-corpus version (1.9+), we have modified it to allow to use a custom
      apparmor profile instead of inject it's own and broken one.

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

- Clone makina-states, even if not installing it on you host

.. code-block:: bash

    mkdir /srv/mastersalt && cd /srv/mastersalt
    git clone http://github.com/makinacorpus/makina-states.git

- Create the base makinacorpus/makina-states image

.. code-block:: bash

 cd /srv/mastersalt/makina-states
 ./docker/stage.py
 docker tag makinacorpus/makina-states-ubuntu-vivid:candidate makinacorpus/makina-states-ubuntu-vivid:latest


Build a kubernetes cluster
--------------------------
Behind the scenes a kubernetes cluster involve those following services all run
inside containers:

    * docker/distribution
    * redis
    * etcd
    * kubemaster
    * kubeproxy

To build something more powerfull that the basic makina-states images and stop
playing by hand, you ll want to build a kubernetes cluster.

Either do this on a VM based on ubuntu 14-04 and onwards or on baremetal if you
know makina-states.

Amongst others:

    * Be aware that this will install and configure firewalld, a by-default
      restrictive firewall.
    * This will install and configure lot of prerequisites needed by
      makina-states

* Install makina-states and initialize mastersalt
* Install docker via makina-states

Adapt your /srv/mastersalt-pillar/database.sls

    mastersalt-run -lall mc_cloud_compute_node.orchestrate node=$(hostname -f)

* Install etcd
* Install
