saltstates makina tree
===========================

.. contents::

About
--------
- This is a consistent collection of states to deploy our infrastructure from start to end.
- We have not got on the formula way to provide this consistency.
- Most of the configuration should be done using pillar.

Travis badge
=============
.. image:: https://travis-ci.org/makinacorpus/makina-states.png
    :target: http://travis-ci.org/makinacorpus/makina-states

What states can be found in makina-states
-----------------------------------------
The state to read immediatly is `servers.base <https://github.com/makinacorpus/makina-states/blob/master/servers/base.sls>`_.
Most configuration are in `localsettings <https://github.com/makinacorpus/makina-states/blob/master/localsettings`_.
Most states are in `services <https://github.com/makinacorpus/makina-states/blob/master/services>`_.
The most outstanding features are:

    - Bootstrapping our saltstates binaries
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
- Include things in **/srv/salt/top.sls** or in **grains** or **pillar** keys to enable specific makina-states to run.
- Re Run top.sls Top file (**state.highstate**):
  This file is in charge to setup all what is not installed yet.
- **For mastersalt managed box, we use salt-cloud to bootstrap distant minions and not the bootstrapscript directly**.

Install a new salt-managed box
-------------------------------
- To install our base salt installation, just run this script as **root**, please read next paragraphs before running any command.
- All our installs run 2 instances of salt: **mastersalt** and **salt**
- You will nearly never have to handle much with the **mastersalt** part
- The two instances will have to know where they run to first make the system
  ready for them.
- All the behavior of the script is controlled via environment variables or command line arguments.
- That's why you will need to tell which daemons you want and on what kind of machine you are installing on.
- Salt flavors are known as **controllers** and machine kinds as **nodetypes**.

    - The default nodetype is **server**.
    - The default installed **controller** flavor is **salt**, and in other words, we do not install **mastersalt** by default.

- You'll also have to set the daemon id. The default choice for **--minion-id** is the current machine hostname
  but you can force it to set a specific minion id.

- You choice for **--nodetype** and **--mastersalt-nodetype** is certainly one of **server**, **vm**, **vagrantvm** or **devhost**.

    - The default is **server**.
    - **vm** matches a VM (not baremetal)
    - If you choose **devhost**, this mark the machine as a development machine
      enabling states to act on that, by example installation of a test local-loop mailer.
    - If you choose **vagrantvmt**, this mark the machine as a vagrant virtualbox.

- You default choice for **SALT_CONTROLLER** is certainly one of **salt_master** or **salt_minion**.
- For salt, you have some extra parameters (here are the environment variables, but you have also
  command line switches to set them

    - **--salt-master-dns**; hostname (FQDN) of the linked master
    - **--salt-master-port**: port of the linked master
    - **--mastersalt**: is the mastersalt hostname (FQDN) to link to
    - **--mastersalt-master-port**: overrides the port for the distant mastersalt server which is 4606 usually (read the script)

Quality Assurance
******************
This will run:

    - unit tests
    - linters
    - install all states

For this reason, run those states only a box that you ll trash afterwards

On a provisionned box, run::

    ./boot-salt.sh -C -s -S --tests

It will run all the sls found in ``makina-states.tests``.


Usage
*********
Short overview::

    ./boot-salt.sh --help

Detailed overview::

    ./boot-salt.sh --long-help

EXAMPLES
*********
Get the script::

    wget http://raw.github.com/makinacorpus/makina-states/master/_scripts/boot-salt.sh

If you want to install only a minion::

    ./boot-salt.sh --no-salt-master --salt-master-dns IP.OR.DNS.OF.SALT.MASTER [--salt-master-port "PORT OF MASTER  IF NOT 4506"]

If you want to install salt on a bare server::

    ./boot-salt.sh --n server

If you want to install salt on a vm::

    ./boot-salt.sh --n vm

If you want to install salt on a machine flaggued as a devhost (server + dev mode)::

    ./boot-salt.sh --n devhost

If you want to install salt on a server and then wire it to a mastersalt master running on another machine::

    ./boot-salt.sh --mastersalt mastersalt.company.net

If you want to install and test test mastersalt system locally to your box, when it is set, you need to edit the pillar to change it::

    ./boot-salt.sh --mastersalt-master --mastersalt localhost

To skip the automatic code update/upgrade::

    ./boot-salt.sh -S

To switch on a makina-states branch, like the **stable** branch in production::

    ./boot-salt.sh -b  stable

SUMUP
*******

    - To install on a server (default env=server, default boot=salt_master)::

        ./boot-salt.sh

    - To install on a dev machine (env=devhost, default boot=salt_master)::

        ./boot-salt.sh -n devhost

    - To install on a server and use mastersalt::

        ./boot-salt.sh --mastersalt mastersalt.makina-corpus.net

boot-salt.sh will try remember to remember how you configured makina-states.
If it suceeds to find enougth information (nodetype, salt installs, branch), it will automaticly guess the parameters by it self.
In other words, you will just have to type **boot-salt.sh** and verify settings next time you ll use it.


Running project states
------------------------------
- At makina corpus where the states tree resides in a salt branch of our projects, we can use this script to deploy a project from salt to the project itself.
- For this, prior to execute the script, you can tell which project url, name, and branch to use.
- See also https://github.com/makinacorpus/salt-project
- You can safely use the script multiple times to install projects (even long first after installation)
- In most case, if the script has run once, you can relaunch it and it may have enought information on the system
  to guess how to run itself, just verify the variables sum up at the beginning.

::

    mkdir /srv/pillar
    # $ED is your default editor, rplace with nano, vim or anything
    # if the default is not the one you want
    $ED /srv/pillar/top.sls
    $ED /srv/pillar/foo.sls
    export NAME="foo" (default: no name)
    export URL"GIT_URL" (default: no url)
    export BRANCH="master" (default: salt)
    export TOPSTATE="deploy.foo" (default: no default but test if top.sls exists and use it")
    boot-salt.sh --project-url $URL --project-branch $BRANCH --project-state $TOPSTATE

Optionnaly you can edit your pillar in **/srv/pillar**::

    $ED /srv/pillar/top.sls

Then run higtstate or any salt cmd::

    salt-call state.highstate

According to makinacorpus projects layouts, your project resides in:

    - **/srv/projects/$PROJECT_NAME**: root prefix
    - **/srv/projects/$PROJECT_NAME/salt**: the checkout of the salt branch
    - **/srv/projects/$PROJECT_NAME/project**:  should contain the main project code source and be initialised by your project top.sls
    - **/srv/salt/makina-projects/$PROJECT_NAME**: symlink to the salt branch

Example to install the most simple project::

    URL="https://github.com/makinacorpus/salt-project.git"  BRANCH="sample-salt" NAME="sample"
    boot-salt.sh --project-url $URL --project-branch $BRANCH

Mastersalt specific
-----------------------
If you runned the mastersalt install, tell an admin to accept the mastersalt-minion key on the MasterofMaster::

    mastersalt-key -A

you can then do any further needed configuration from mastersalt::

    mastersalt 'thisminion' state.show_highstate
    mastersalt 'thisminion' state.highstate

Or from local when admins have configured things::

    salt-call -c /etc/mastersalt  state.show_highstate

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
        from zc..buildout.easy_install import realpath
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
