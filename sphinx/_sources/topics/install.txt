Installation & basic usage
==========================
Briefing
----------
**For now, use Ubuntu >= 14.04.**.
Makina-States can be ported to any linux based OS,
but we here use ubuntu server and this is the only supported system for now.
It can be used in any flavor, lxc, docker, baremetal, kvm, etc.

To install our base salt installation, you have to choose between different modes of operations
tweakable via the **nodetype** setting:

    - The regular preset modes manages the system configuration from end to end, from
      the system, to makina-states, including the saltstack/salt/ansible installation
      itself.
    - The special ``scratch`` mode manages only the saltstack + makina-states
      configuration by default, so it's up to you to apply any other state
      but do not touch much to the system itself more than installing the
      scripts for wiring makina-states

**Makina-states do not use regular salt daemons to operate remotely
but an ansible bridge that copy the pillar and use salt-call locally
directly on the remote box**

Reminder
---------
- Makina-states is based on "nodetypes presets" that are prebundled
  collections of makina-states states to apply to the system.
- On those nodetypes, we manage "controllers", aka the states which configure
  salt & ansible for operation
- On those nodetypes, we may configure "localsettings" like ssl, vim, git, &
  basepackages or network configurations. If any other preset than **scratch**
  has been activated, many localsettings will be applied by default (see
  mc_states/modules/localsettings.py:registry)
- After all of the previous steps, we may configure services like sshd,
  crond, or databases. If we are on the **scratch** mode, no services
  are configured by default.
- Eventually, we may by able to install projects via mc_project.
  A project is just a classical code repository which has a ".salt" and/or
  ansible playbooks/roles folder commited with enougth information on how
  to deploy it.

Details
--------
Just run the **_scrits/boot-salt.sh** script as **root**,

Please read next paragraphs before running any command.

- All the behavior of the script can be controlled via environment variables or command line arguments switches.
- You will need to tell on what kind of environment you are installing on (the nodetype).
- You'll also have to set the **minion id**. The default choice for **--minion-id** is the current machine hostname.
  You should keep this naming scheme unless you have a good reason to change it.

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

.. _project_regular_modes:

Regular modes (via boot-salt.sh)
--------------------------------
boot-salt.sh will try to remember how you configured makina-states on each run.
It stores configs in :

    - installdir/etc/makina-states

Indeed while running, the script try to find enougth information (nodetype, salt installs, branch),
and will automaticly guess & store the parameters by itself.

In other words, you will just have to type **boot-salt.sh**, and verify settings the next time you ll use it.

**REMEMBER THAT FOR NOW YOU HAVE TO USE UBUNTU >= 14.04.**

Download
~~~~~~~~~
Get the script::

    wget http://raw.github.com/makinacorpus/makina-states/v2/_scripts/boot-salt.sh

Short overview::

    ./boot-salt.sh --help

Detailed overview::

    ./boot-salt.sh --long-help

CLI Exemples
~~~~~~~~~~~~~
If you want to install only a minion which will be connected to a remote
mastersalt master::

    ./boot-salt.sh

If you want to install salt on a machine flaggued as a devhost (server + dev mode)::

    ./boot-salt.sh --n devhost

If you want to manage from end to end your server, select also the ``laptop`` preset
nodetype::

    ./boot-salt.sh -n laptop

To skip the automatic code update/upgrade::

    ./boot-salt.sh -S

To switch on a makina-states branch, like the **v2** branch in production::

    ./boot-salt.sh -b v2

Upgrade
+++++++
Upgrade will:

    - Run predefined & scheduled upgrade code
    - Uupdate makina-states repositories in /srv/salt & /srv/makina-states
    - Update core repositories (like salt code source in /srv/makina-states/src/salt)
    - Do the highstates (salt and masterone if any)

::

    boot-salt.sh -C --highstates

Activating another nodetype preset after installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If you installed the **scratch** preset and want to switch to another preset::

    salt-call state.sls makina-states.nodetypes.<your_new_preset>

If you installed a preset and want to switch to another preset:

    - edit **etc/makina-states/nodetype** and put your new preset
    - edit **etc/*/makina-states/nodetypes.yaml** and set to false your old
      preset
    - Finally, run::

        salt-call state.sls makina-states.nodetypes.<your_new_preset>

