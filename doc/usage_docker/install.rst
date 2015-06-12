.. _install_docker:

Install a makina-states docker environement
============================================
Basic development  installation
-------------------------------
- For ubuntu, you best bet is to use something >= Ubuntu 14.04 with a recent kernel (from enablement stack)
- Install docker by reading your distribution guidelines for that purpose

    - Eg on ubuntu

        apt-get install lxc docker

    - Replace docker by makina-corpus version (1.7+), we have modified it to allow to use a custom
      apparmor profile instead of inject it's own and broken one.

        - The sources are `here@github <https://github.com/makinacorpus/docker.git>`_.
        - We provide a `prebuilt binary for linux <https://github.com/makinacorpus/docker/releases/download/mc_1/docker>`_.::

            cp /usr/bin/docker /usr/bin/docker.dist
            curl -L --insecure -s https://github.com/makinacorpus/docker/releases/download/mc_1/docker -o /usr/bin/docker
            # or wget https://github.com/makinacorpus/docker/releases/download/mc_1/docker -O /usr/bin/docker
            chmod +x /usr/bin/docker

- If you are on Ubuntu or any system protected by **apparmor**, you ll have to tweak your apparmor installation.
  If you are not configuring your system via makina-states, you can however bring back the profile quite easily::

    mkdir -pv /etc/apparmor.d/abstractions/lxc
    curl -L --insecure -s https://raw.githubusercontent.com/makinacorpus/makina-states/master/files/etc/apparmor.d/abstractions/lxc/powercontainer-base -o /etc/apparmor.d/abstractions/lxc/powercontainer-base
    curl -L --insecure -s https://raw.githubusercontent.com/makinacorpus/makina-states/master/files/etc/apparmor.d/abstractions/dockercontainer -o /etc/apparmor.d/abstractions/dockercontainer
    service apparmor restart

- Clone makina-states, even if not installing it on you host
::

    mkdir /srv/mastersalt && cd /srv/mastersalt
    git clone http://github.com/makinacorpus/makina-states.git

- Create the base makinacorpus image


bootstrap a django project
---------------------------
TBD

bootstrap a drupal project
---------------------------
TBD

