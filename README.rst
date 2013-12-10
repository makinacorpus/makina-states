saltstates makina tree
===========================

.. contents::

About
--------
- This is a consistent collection of states to deploy our infrastructure from start to end.
- We have not got on the formula way to provide this consistency.
- Most of the configuration should be done using pillar.

What states can be found in makina-states
-----------------------------------------
Most states are in ``makina.services``.
The most outstanding features are:

    - Bootstrapping our saltstack binaries
    - Managing /etc/hosts
    - Managing network (debian-style)
    - Integrating system with an ldap server
    - Managing ssh & users
    - Configuring ntp
    - Configuring shell
    - Configuring localrc (/etc/rc.local)
    - Configuring git
    - Configuring git to correctly attack our gitorious
    - Configuring vim
    - Configuring sudo
    - Managing shorewall
    - Managing lxc containers
    - Managing docker containers
    - Configuring apache
    - Configuring php
    - Configuring dovecot
    - Configuring postfix
    - Configuring mysql
    - Configuring postgresql
    - Configuring tomcat
    - Configuring solr
    - Configuring bacula file daemon

Follow the instruction and you will have then a salt-master and a salt-minion waiting for instructions.

Worflow in MkC deployments
-----------------------------
- Run makina-states bootstrap script
  This script will provide an up and running salt installation
- Include things in **/srv/salt/top.sls** & **/srv/salt/setup.sls**:
  Those file tie to specific minions the configuration to apply to them.

    - All projects must have a pre-configured setup and a top file (in salt TOP format) to include in TOPLEVEL setup & tops.

- Run setup.sls Top file:
  This file is in charge to setup the code source and what is only related to make salt states work
- Run top.sls Top file:
  This file is in charge to setup all what is not installed yet.

Install a new salt-managed box
-------------------------------
If you want to install salt directly on your machine::

    export SALT_BOOT=""

If you want to install salt on a bare server::

    export SALT_BOOT="server"

If you want to install salt on a vm::

    export SALT_BOOT="vm"

If you want to install salt on a machine flaggued as a devhost (server + dev mode)::

    export SALT_BOOT="devhost"

If you want to install salt on a server and then wire it to a mastersalt master running on another machine::

    export MASTERSALT="http://mastersalt"
    eg : export MASTERSALT="http://mastersalt.makina-corpus.net"

If you want to install and test test mastersalt system loclly to your box::

    export MASTERSALT="localhost" MASTERSALT_BOOT="master"

- **MASTERSALT** is the mastersalt host to link to
- **MASTERSALT_PORT** overrides the port for the distant mastersalt server
  which is 4606 usually (read the script)
- **MASTERSALT_BOOT=minion|master** instructs to install a mastersalt master or minion on  localhost. In master mode, it also add alocal mastersalt minion.

To install our base salt installation, just run this script as **ROOT**, please read next paragraphe before running this command::

    wget http://raw.github.com/makinacorpus/makina-states/master/_scripts/boot-salt.sh -O - | bash
    or
    wget http://raw.github.com/makinacorpus/makina-states/master/_scripts/boot-salt.sh
    chmod +x boot-salt.sh
    ./boot-salt.sh

::

    . /etc/profile

This will do install prereq, salt, and accept the key locally for the local master/minion, and maybe isntall a project after

Running project states
------------------------------
- At makina corpus where the states tree resides in a salt branch of our projects, we can use this script to deploy a project from salt to the project itself.
- For this, prior to execute the script, you can tell which project url, name, and branch to use.
- You can optionnaly tell which setup sls state and which top sms state to bootstrap.
- See also https://github.com/makinacorpus/salt-project
- You can safely use the script multiple times to install projects (even long first after installation)

::

    mkdir /srv/pillar
    $ED /srv/pillar/top.sls
    $ED /srv/pillar/foo.sls
    export PROJECT_NAME="foo" (default: no name)
    export PROJECT_URL="GIT_URL" (default: no url)
    export PROJECT_BRANCH="master" (default: salt)
    export PROJECT_SETUPSTATE"deploy.foo" (default: no default but test if setup.sls exists and use it")
    export PROJECT_TOPSTATE="deploy.foo" (default: no default but test if top.sls exists and use it")
    wget http://raw.github.com/makinacorpus/makina-states/master/_scripts/boot-salt.sh -O - | bash

Optionnaly you can edit your pillar in **/srv/pillar**::

    $ED /srv/pillar/top.sls

Then run higtstate or any salt cmd::

    salt-call state.highstate

According to makinacorpus projects layouts, your project resides in:

    - **/srv/projects/$PROJECT_NAME**: root prefix
    - **/srv/projects/$PROJECT_NAME/salt**: the checkout of the salt branch
    - **/srv/projects/$PROJECT_NAME/project**:  should contain the main project code source and be initialised by your project setup.sls
    - **/srv/salt/makina-projects/$PROJECT_NAME**: symlink to the salt branch

Example to install the most simple project::

    PROJECT_URL="https://github.com/makinacorpus/salt-project.git" \
    PROJECT_BRANCH="sample-salt" PROJECT_NAME="sample" \
    wget http://raw.github.com/makinacorpus/makina-states/master/_scripts/boot-salt.sh -O - | bash

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

    -:server: ::

        /srv/salt/makina-states/bin/salt-call -lall --local state.sls makina-states.services.bootstrap_server

    -:dev VM or docker or virtualbox: ::

        /srv/salt/makina-states/bin/salt-call -lall --local state.sls makina-states.services.bootstrap_vm

    -:server wired to mastersalt: ::

        /srv/salt/makina-states/bin/salt-call -lall --local state.sls makina-states.services.bootstrap_mastersalt
Then ::

    . /etc/profile


- On  ``thelocalbox.domain.net``::

    salt-key -A



Troubleshooting
=================



::

    Generated script '/srv/salt/makina-states/bin/buildout'.
    Launching buildout for salt initialisation
    Traceback (most recent call last):
      File "bin/buildout", line 17, in <module>
        import zc.buildout.buildout
      File "/srv/salt/makina-states/eggs/zc.buildout-1.7.1-py2.7.egg/zc/buildout/buildout.py", line 40, in <module>
        import zc.buildout.download
      File "/srv/salt/makina-states/eggs/zc.buildout-1.7.1-py2.7.egg/zc/buildout/download.py", line 20, in <module>
        from zc.buildout.easy_install import realpath
      File "/srv/salt/makina-states/eggs/zc.buildout-1.7.1-py2.7.egg/zc/buildout/easy_install.py", line 31, in <module>
        import setuptools.package_index
      File "/usr/local/lib/python2.7/dist-packages/distribute-0.6.24-py2.7.egg/setuptools/package_index.py", line 157, in <module>
        sys.version[:3], require('distribute')[0].version
      File "build/bdist.linux-x86_64/egg/pkg_resources.py", line 728, in require
        supplied, ``sys.path`` is used.
      File "build/bdist.linux-x86_64/egg/pkg_resources.py", line 626, in resolve
        ``VersionConflict`` instance.
    pkg_resources.DistributionNotFound: distribute
    Failed buildout

Update your system setuptools install to match latest setuptools (distribute + setuptools fork reunion)::

    sudo easy_install -U setuptools


