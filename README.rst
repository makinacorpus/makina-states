saltstates makina tree
===========================

.. contents::

Prerequisite
----------------
- Install those packages::

    apt-get install -y build-essential m4 libtool pkg-config autoconf gettext bzip2 groff man-db automake libsigc++-2.0-dev tcl8.5
    apt-get install -y git python-dev swig libssl-dev libzmq-dev

- Be sure to configure correctly the machine **FQDN** ( which will determine the **MINION_ID**.

``$ hostname`` should return::

    machine.domain (like: toto.domain.net)

- Create the salt top & develop code::

    mkdir  -p /srv/pillar /srv/salt
    git clone https://github.com/makinacorpus/makina-states.git /srv/salt/makina-states

Install a new salt-managed box
---------------------------------
ON A DEV BOX
++++++++++++++++++++++++++++++++++++++++++
- Run the install buildout::

    cd /srv/salt/makina-states
    python bootstrap.py
    bin/buildout

- Install the base salt states infastructure::

    /srv/salt/makina-states/bin/salt-call -lall --local state.sls makina-states.services.bootstrap
    . /etc/profile

- You ll have then a saltmaster/minion waiting for insttructions, up to you to mangle a top.sls to start from

On a server
+++++++++++++++++++++++++++
Scripted
~~~~~~~~~~~~
run the script::

    ./_scripts/boot-salt.sh

Which does install prereq, salt, and accept the key locally for the local master/minion

Tell an admin to accept the mastersalt-minion key on the MasterofMaster::

    mastersalt-key -A

Do any further needed configuration from mastersalt::

    mastersalt 'thisminion' state.show_highstate
    mastersalt 'thisminion' state.highstate

fallback: manual mode
~~~~~~~~~~~~~~~~~~~~~~
- Run the install buildout::

    cd /srv/salt/makina-states
    python bootstrap.py
    bin/buildout

- Install the base salt states infastructure::

    /srv/salt/makina-states/bin/salt-call -lall --local state.sls makina-states.services.bootstrap_server
    . /etc/profile


- On  ``thelocalbox.domain.net``::

    salt-key -A

What states can be found in makina-states
-----------------------------------------
Most states are in ``makina.services``.
Outstanding features are:

    - Bootstrapping our saltstack binaries
    - Managing lxc containers
    - Managing /etc/hosts
    - Managing network (debian-style)
    - Managing shorewall
    - Managing ssh & users
    - Integrating system with an ldap server
    - Configuring ntp
    - Configuring sudo
    - Configuring git to correctly attack our gitorious
    - Configuring bacula file daemon
