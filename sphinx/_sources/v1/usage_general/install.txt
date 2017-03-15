Installation & basic usage
==========================
Briefing
----------

**For now, use Ubuntu >= 14.04.**.
Makina-States can be ported to any linux based OS,
but we here use ubuntu server and this is the only supported system for now.
It can be used in any flavor, lxc, docker, baremetal, kvm, etc.

To install our base salt installation, you have to choose between 3 main mode of operations:

The :ref:`regular modes <project_regular_modes>` light mode via boot-salt.sh:

    - The regular preset modes manages the system configuration from end to end, from
      the system, to makina-states, including the saltstack/salt installation
      itself.
    - The special ``scratch`` mode manages only the saltstack + makina-states
      configuration by default, and it's up to you to apply any other state

The :ref:`light mode <project_light_mode>` light mode via install_makina_states.sh:

    - Use makina-states where salt is already installed 
      and where it's install has not to have to be done via
      makina-states itself.

Reminder
---------
- Makina-states is based on "nodetypes presets" that are prebundled
  collections of makina-states states to apply to the system.
- On those nodetypes, we may manage "controllers", aka the salt daemons.
- On those nodetypes, we may configure "localsettings" like vim, git, &
  basepackages or network configurations. If any other preset than **scratch**
  has been activated, many localsettings will be applied (see
  mc_states/modules/localsettings.py:registry)
- After all of the previous steps, we may configure services like sshd,
  crond, or databases. If we are on the **scratch** mode, no services
  are configured by default.
- Eventually, we may by able to install projects via mc_project.
  A project is just a classical code repository which has a ".salt" folder
  commited with enougth information on how to deploy it.

Details
--------
just run the **_scrits/boot-salt.sh** script as **root**,

Please read next paragraphs before running any command.

- In most cases, all our production installs run 2 instances of salt: **mastersalt** and **salt** which can be be in **asterless** or **remote** mode.
  In this mode, certains states are only reachable from the mastersalt daemons
  (the low levels which will can break the system and have to be done via
  sysadmin).
- In some case, you can install only the **salt** side, and both mastersalt &
  salt configurations will be available for use in this mode.

- As a sole developer, You will nearly never have to handle much with the **mastersalt** part unless you are going to be very low-level.
- All the behavior of the script can be controlled via environment variables or command line arguments switches.
- That's why you will need to tell which daemons you want (minion/master) and on what kind of environment you are installing on (the nodetype).
- You'll also have to set the **minion id**. The default choice for **--minion-id** is the current machine hostname.
  You should keep this naming scheme unless you have a good reason to change it.

- Default salt install is **masterless (standalone)**.
- Default mastersalt install is **remote (connected)**.

- Your choice for ``\-\-nodetype`` is certainly one of:

    - **scratch** manages by default only the salt installation and configuration.
      You ll want to activate this mode if you want to apply explicitly your
      states without relying of default nodetypes configuration.
    - **server (default)** matches a baremetal server, and manage it from end to end (base
      packages, network, locales, sshd, crond, logrotate, etc, by default)
    - **vm** matches a VM (not baremetal), this is mostly like **server**.
    - **lxccontainer** matches a VM (not baremetal), this is mostly like **server**.
    - **laptop** is like server but also install packages for working on a
      developement machine (prebacking a laptop for a dev)
    - **dockercontainer** matches a VM (not baremetal), this is mostly like **server**, but install & preconfigure circus to manage daemons.
    - **devhost** is suitable for a development machine enabling states to act on that,
      by example installation of a test local-loop mailer.
    - **vagrantvm** is suitable to flag vagrant boxes and is a subtype of
      devhost

- For configuring all salt daemons, you have some extra parameters (here are the environment variables, but you have also
  command line switches to set them

    - **\-\-salt-master-dns**; hostname (FQDN) of the linked master
    - **\-\-salt-master-port**: port of the linked master
    - **\-\-mastersalt**: is the mastersalt hostname (FQDN) to link to
    - **\-\-mastersalt-master-port**: overrides the port for the distant mastersalt server which is 4606 usually (read the script)

.. _project_regular_modes:

Regular modes (via boot-salt.sh)
--------------------------------
boot-salt.sh will try to remember how you configured makina-states on each run.
It stores configs in :

    - /etc/salt/makina-states & if available /etc/mastersalt
    - /etc/makina-states

Indeedn while running, the script try to find enougth information (nodetype, salt installs, branch),
and will automaticly guess & store the parameters by itself.

In other words, you will just have to type **boot-salt.sh**, and verify settings the next time you ll use it.

**REMEMBER THAT FOR NOW YOU HAVE TO USE UBUNTU >= 14.04.**

Download
~~~~~~~~~
Get the script::

    wget http://raw.github.com/makinacorpus/makina-states/master/_scripts/boot-salt.sh

Short overview::

    ./boot-salt.sh --help

Detailed overview::

    ./boot-salt.sh --long-help

CLI Exemples
~~~~~~~~~~~~~
If you want to install only a minion which will be connected to a remote
mastersalt master::

    ./boot-salt.sh --mastersalt <MASTERSALT_FQDN> \
        [--mastersaltsalt-master-port "PORT OF MASTER  IF NOT 4506"]

If you want to install salt on a bare server, without mastersalt::

    ./boot-salt.sh --no-mastersalt

If you want to install salt on a machine flaggued as a devhost (server + dev mode)::

    ./boot-salt.sh --n devhost

If you want to install and test test mastersalt system locally to your box::

    ./boot-salt.sh --mastersalt-master --mastersalt $(hostname -f)

If you want to manage from end to end your server, select also the ``laptop`` preset
nodetype::

    ./boot-salt.sh --mastersalt <MASTERSALT_FQDN> \
        [--mastersaltsalt-master-port "PORT OF MASTER  IF NOT 4506"] -n laptop

To skip the automatic code update/upgrade::

    ./boot-salt.sh -S

To switch on a makina-states branch, like the **stable** branch in production::

    ./boot-salt.sh -b stable



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


.. _project_light_mode:

Light mode (via install_makina_states.sh)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This is mainly needed to integrate Makina-States within a pre-existing
salt infrastructure (via install_makina_states.sh).


Basically makina states contains:

    - a python egg
    - a lot of custom salt modules of different types (execution, grains,
      states, cloud, etc.)
    - a collection of formulaes

To enable it into your salt infrastructure:

    - You have to put it in your salt_root to activate the formulaes:
    - You have to install python dependencies (see the script) and the mc_states
      python package (included in makina-states)
    - You have to link all custom salt modules to your salt root and
      synchronnise your minions caches.

We provide a convenient helper for this purpose called **_scripts/install_makina_states.sh**::

    wget \
     http://raw.github.com/makinacorpus/makina-states/master/_scripts/install_makina_states.sh
    export SALT_ROOT="/srv/salt" # whereever it is
    ./install_makina_states.sh

The script can safely be recalled after each makina-states "git pull" to relink the
updated modules.


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

