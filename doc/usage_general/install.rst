Installation & basic usage
==========================
Briefing
----------
To install our base salt installation, you have to choose between 3 main mode of operations:

The regular modes via boot-salt.sh:

    - The regular preset modes manages the machine configuration from end to end, from
      the system, to makina-states, including the saltstack/salt installation
      itself.
    - The special "scratch" mode manages only the saltstack + makina-states
      configuration by default, and it's up to you to apply any other state

The light mode via install_makina-states.sh:

    - The "light" mode goal is to use makina-states where salt is already
      installed and where it's install has not to have to be done via
      makina-states itself.

Reminder
---------
Always remember:

    - Makina-states is based on "nodetypes presets" that are prebundled
      collections of makina-states states to apply to a machine.
    - On those nodetypes, we may manage "controllers", aka the salt daemons.
    - On those nodetypes, we may configure "localsettings" like vim, git, &
      basepackages or network configurations
    - After all of the previous steps, we may configure services like sshd,
      crond, or databases
    - Eventually, we may install projects.

Details
--------
just run the **_scrits/boot-salt.sh** script as **root**,

Please read next paragraphs before running any command.

- In most cases, all our production installs run 2 instances of salt: **mastersalt** and **salt** which can be be in **asterless** or **remote** mode.
  In this mode, certains states are only reachable from the mastersalt daemons
  (the low levels which will can break the machine and have to be done via
  sysadmin).
- In some case, you can install only the **salt** side, and both mastersalt &
  salt configurations will be available for use in this mode.

- As a sole developer, You will nearly never have to handle much with the **mastersalt** part unless you are going to be very low-level.
- The two instances will have to know where they run to first make the system ready for them.
- All the behavior of the script can be controlled via environment variables or command line arguments switches.
- That's why you will need to tell which daemons you want (minion/master) and on what kind of machine you are installing on (vm/vagrant/baremetal).
- You'll also have to set the **minion id**. The default choice for **--minion-id** is the current machine hostname.
  You should keep this naming scheme unless you have a good reason to change it.

- Default salt install is **masterless (standalone)**.
- Default mastersalt install is **remote (connected)**.

- You choice for **--nodetype** is certainly one of **scratch**, **server**, **vm**, **lxccontainer**, **dockercontainer**, **vagranvm** or **devhost**.

    - **scratch** (default) manages by default only the salt installation and configuration.
    - **server** matches a baremetal server, and manage it from end to end (base
      packages, network, locales, sshd, crond, logrotate, etc, by default)
    - **vm** matches a VM (not baremetal), this is mostly like **server**.
    - **lxccontainer** matches a VM (not baremetal), this is mostly like **server**.
    - **laptop** is like server but also install packages for working on a
      developement machine (prebacking a laptop for a dev)
    - **dockercontainer** matches a VM (not baremetal), this is mostly like **server**, but install & preconfigure circus to manage daemons.
    - **devhost**  marks the machine as a development machine enabling states to act on that, by example installation of a test local-loop mailer.
    - **vagrantvmt**  marks the machine as a vagrant virtualbox.

- For configuring all salt daemons, you have some extra parameters (here are the environment variables, but you have also
  command line switches to set them

    - **\-\-salt-master-dns**; hostname (FQDN) of the linked master
    - **\-\-salt-master-port**: port of the linked master
    - **\-\-mastersalt**: is the mastersalt hostname (FQDN) to link to
    - **\-\-mastersalt-master-port**: overrides the port for the distant mastersalt server which is 4606 usually (read the script)

Usage
-----
boot-salt.sh will try to remember how you configured makina-states on each run.
It stores configs in :

    - /etc/salt/makina-states & if available /etc/mastersalt
    - /etc/makina-states

Download
~~~~~~~~~
Get the script::

    wget http://raw.github.com/makinacorpus/makina-states/master/_scripts/boot-salt.sh

Short overview::

    ./boot-salt.sh --help

Detailed overview::

    ./boot-salt.sh --long-help

Install
~~~~~~~
If you want to install only a minion which will be connected to a remote
mastersalt master::

    ./boot-salt.sh --mastersalt <MASTERSALT_FQDN> [--mastersaltsalt-master-port "PORT OF MASTER  IF NOT 4506"] -n server

If you want to install salt on a bare server, without mastersalt::

    ./boot-salt.sh --no-mastersalt

If you want to install salt on a machine flaggued as a devhost (server + dev mode)::

    ./boot-salt.sh --n devhost

If you want to install and test test mastersalt system locally to your box::

    ./boot-salt.sh --mastersalt-master --mastersalt $(hostname -f)

If you want to manage from end to end your server, select also the "server" preset
nodetype::

    ./boot-salt.sh --mastersalt <MASTERSALT_FQDN> [--mastersaltsalt-master-port "PORT OF MASTER  IF NOT 4506"] -n server

Useful switches
++++++++++++++++

To skip the automatic code update/upgrade::

    ./boot-salt.sh -S

To switch on a makina-states branch, like the **stable** branch in production::

    ./boot-salt.sh -b stable

If it suceeds to find enougth information (nodetype, salt installs, branch), it will automaticly guess the parameters by it self.
In other words, you will just have to type **boot-salt.sh** and verify settings next time you ll use it.

Upgrade
+++++++
Upgrade will:

    - Run predefined & scheduled upgrade code
    - Uupdate makina-states repositories in /srv/salt & /srv/makina-states
    - Update core repositories (like salt code source in /srv/makina-states/src/salt)
    - Redo the daemon configuration if necessary
    - Redo the daemon association if necessary
    - Do the highstates (salt and masterone if any)

::

    boot-salt.sh -C --upgrade

Integrate makina-states with a pre-existing salt infrastructure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Basically makina states is:

    - a python egg
    - a container for custom salt modules
    - a collection of formulaes

To install it:

    - you have to put it in your salt_root to activate the formulaes:
    - you have to install python dependencies (see the script) and the mc_states
      python package (included in makina-states)
    - you have to link all custom salt modules to your salt root and
      synchronnise your minions caches.

This is the purpose of the **install_makina_states.sh** script::

    wget http://raw.github.com/makinacorpus/makina-states/master/_scripts/install_makina_states.sh
    export SALT_ROOT="/srv/salt" # whereever it is
    ./install_makina_states.sh

The script can safely be recalled after each makina-states "git pull" to relink the
modules.


Activating another nodetype preset after installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If you installed the **scratch** preset and want to switch to another preset::

    [master]salt-call [--local] state.sls makina-states.nodetypes.<your_new_preset>

If you installed a preset and want to switch to another preset:

    - edit **/etc/makina-states/nodetype** and put your new preset
    - edit **/etc/*/makina-states/nodetypes.yaml** and set to false your old
      preset
    - Finally, run::

        [master]salt-call [--local] state.sls makina-states.nodetypes.<your_new_preset>

