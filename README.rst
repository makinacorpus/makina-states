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
- To install our base salt installation, just run this script as **ROOT**, please read next paragraphes before running any command.
- All our installs run 2 instances of salt: **mastersalt** and **salt**
- You will nearly never have to handle much with the **mastersalt** part
- The two instances will have to know where they run to first make the system
  ready for them.
- All the behavior of the script is controlled via environment variables.
- That's why you will need to set at least which **SALT_BOOT** and **SALT_ENV** you want, and maybe
  **MASTERSALT_BOOT** and **MASTERSALT_ENV**.
- You default choice for **SALT_BOOT_ENV** and **MASTERSALT_BOOT_ENV** is certainly one of **server**, **vm**  or **devhost**.

    - The default is **server**.
    - **vm** matches a VM (not baremetal)
    - If you choose **devhost**, this mark the machine as a devloppment machine
      enabling states to act on that, by example installation a test mailer.

- You default choice for **MASTERSALT_BOOT_ENV** is the same that for **SALT_BOOT_ENV**.

  - If not set, it will default to **SALT_BOOT_ENV**

- You default choice for **SALT_BOOT** is certainly one of **salt_master** or **salt_minionr**.

    - The default is **salt_server**.
    - **salt_minion** will only install a minion and you will need to set:

        - **SALT_MASTER_IP**: DNS or ip of the linked master
        - **SALT_MASTER_PORT**: port of the linked master

- You default choice for **MASTERSALT_BOOT** is certainly **mastersalt_minion**.

    - The default is **NOT SET** meaning that we do not install anything of mastersalt by default.
    - **mastersalt_minion** will only install a minion, which will be certainy only what you want
    - The installation process will challenge you for accepting keys on mastersalt-master.
    - **MASTERSALT** is the mastersalt host to link to
    - **MASTERSALT_PORT** overrides the port for the distant mastersalt server which is 4606 usually (read the script)

EXAMPLES
*********
If you want to install only a minion::

    export SALT_BOOT="salt_minion" SALT_MASTER="IP.OR.DNS.OF.SALT.MASTER" SALT_MASTER_PORT="PORT OF MASTER  IF NOT 4506"

If you want to install salt on a bare server::

    export SALT_ENV="server"

If you want to install salt on a vm::

    export SALT_ENV="vm"

If you want to install salt on a machine flaggued as a devhost (server + dev mode)::

    export SALT_ENV="devhost"

If you want to install salt on a server and then wire it to a mastersalt master running on another machine::

    export MASTERSALT="http://mastersalt"
    eg : export MASTERSALT="http://mastersalt.makina-corpus.net"

If you want to install and test test mastersalt system locally to your box::

    export MASTERSALT="localhost" MASTERSALT_BOOT="mastersalt_master"

And finally, **FIRE IN THE HOLE!**::

    wget http://raw.github.com/makinacorpus/makina-states/master/_scripts/boot-salt.sh -O - | bash
    or
    wget http://raw.github.com/makinacorpus/makina-states/master/_scripts/boot-salt.sh
    chmod +x boot-salt.sh
    ./boot-salt.sh

::

    . /etc/profile

To skip the automatic code update/upgrade::

    export SALT_BOOT_SKIP_CHECKOUTS="1"

To skip the automatic setups calls::

    export SALT_BOOT_SKIP_SETUP"1"

SUMUP
*******

    - To install on a server (default env=server, default boot=salt_master)::

        wget http://raw.github.com/makinacorpus/makina-states/master/_scripts/boot-salt.sh -O - | bash

    - To install on a dev machine (env=devhost, default boot=salt_master)::

        export SALT_BOOT_ENV=devhost
        wget http://raw.github.com/makinacorpus/makina-states/master/_scripts/boot-salt.sh -O - | bash

    - To install on a server and use mastersalt::

        export MASTERSALT=mastersalt.makina-corpus.net
        wget http://raw.github.com/makinacorpus/makina-states/master/_scripts/boot-salt.sh -O - | bash

Running project states
------------------------------
- At makina corpus where the states tree resides in a salt branch of our projects, we can use this script to deploy a project from salt to the project itself.
- For this, prior to execute the script, you can tell which project url, name, and branch to use.
- You can optionnaly tell which setup sls state and which top sms state to bootstrap.
- See also https://github.com/makinacorpus/salt-project
- You can safely use the script multiple times to install projects (even long first after installation)
- In most case, if the script has run once, you can relaunch it and it may have enought information on the system
  to guess how to run itself, just verify the variables sum up at the beginning.

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


.. vim: set ft=rst tw=0:
