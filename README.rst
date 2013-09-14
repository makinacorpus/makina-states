saltstates makina tree
===========================

.. contents::

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

Follow the instruction and you ll have then a saltmaster/minion waiting for insttructions, up to you to mangle a top.sls to start from

Install a new salt-managed box din automatic mode
------------------------------------------------------------
If you want to install salt directly on your machine::

    export SALT_BOOT=""

If you want to install salt on a bare server::

    export SALT_BOOT="server"

If you want to install salt on a vm::

    export SALT_BOOT="vm"

If you want to install salt on a server wired to mastersalt::

    export SALT_BOOT="mastersalt"

To install our base salt installation, just run this script as **ROOT**, please read next paragraphe before running this command::

    wget http://raw.github.com/makinacorpus/makina-states/master/_scripts/boot-salt.sh -O - | bash

This will do install prereq, salt, and accept the key locally for the local master/minion, and maybe isntall a project after

Running project states
------------------------------
At makina corpus where the states tree resides in a salt branch of our projects, we can use
You can then download and integrate in ``/srv/salt`` your project saltstack states tree.
Prior to execute the script, you can tell which project, branch and state to bootstrap::

    mkdir /srv/pillar
    $ED /srv/pillar/top.sls
    $ED /srv/pillar/foo.sls
    export PROJECT_URL="GIT_URL" (default: no url)
    export PROJECT_BRANCH="master" (default: salt)
    export PROJECT_TOPSTATE="deploy.foo" (default: state.highstate")
    wget http://raw.github.com/makinacorpus/makina-states/master/_scripts/boot-salt.sh -O - | bash

Or the manual way::

    git clone PROJECT_URL -b salt /srv/salt/project
    rsync -azv /srv/salt/project/ /srv/salt/ && rm -rf /srv/salt/project
    wget http://raw.github.com/makinacorpus/makina-states/master/_scripts/boot-salt.sh -O - | bash

Optionnaly you can edit your pillar in **/srv/pillar**::

    $ED /srv/pillar/top.sls

Then run higtstate or any salt cmd::

    salt-call state.highstate

Mastersalt specific
-----------------------
If you runned the mastersalt install, tell an admin to accept the mastersalt-minion key on the MasterofMaster::

    mastersalt-key -A

you can then do any further needed configuration from mastersalt::

    mastersalt 'thisminion' state.show_highstate
    mastersalt 'thisminion' state.highstate

Or from local when admins have configured things::

    salt-call -c /etc/mastersalt  state.show_highstate

fallback: manual mode
------------------------
Prerequisite
++++++++++++++++++++
- Install those packages::

    apt-get install -y build-essential m4 libtool pkg-config autoconf gettext bzip2 groff man-db automake libsigc++-2.0-dev tcl8.5
    apt-get install -y git python-dev swig libssl-dev libzmq-dev

- Be sure to configure correctly the machine **FQDN** ( which will determine the **MINION_ID**.

``$ hostname`` should return::

    machine.domain (like: toto.domain.net)

- Create the salt top & develop code::

    mkdir  -p /srv/pillar /srv/salt
    git clone https://github.com/makinacorpus/makina-states.git /srv/salt/makina-states

- Run the install buildout::

    cd /srv/salt/makina-states
    python bootstrap.py
    bin/buildout

- Install the base salt states infastructure

    -:Bare developer Computer: ::

        /srv/salt/makina-states/bin/salt-call -lall --local state.sls makina-states.services.bootstrap

    -:server or dev VM or docker or virtualbox: ::

        /srv/salt/makina-states/bin/salt-call -lall --local state.sls makina-states.services.bootstrap_server

    -:server wired to mastersalt: ::

        /srv/salt/makina-states/bin/salt-call -lall --local state.sls makina-states.services.bootstrap_mastersalt
Then ::

    . /etc/profile


- On  ``thelocalbox.domain.net``::

    salt-key -A

