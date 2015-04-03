Installation & basic usage
==========================
Briefing
----------
To install our base salt installation, just run the boot-salt.sh script as **root**,
Please read next paragraphs before running any command.

- All our production installs run 2 instances of salt: **mastersalt** and **salt** which can be be in **asterless** or **remote** mode.
- As a sole developer, You will nearly never have to handle much with the **mastersalt** part uness you also use the **cloudcontroller** part as an admin.
- The two instances will have to know where they run to first make the system ready for them.
- All the behavior of the script can be controlled via environment variables or command line arguments switches.
- That's why you will need to tell which daemons you want (minion/master) and on what kind of machine you are installing on (vm/vagrant/baremetal).
- You'll also have to set the **minion id**. The default choice for **--minion-id** is the current machine hostname.
  You should keep this naming scheme unless you have a good reason to change it.

- Default salt install is **masterless**.
- Default mastersalt install is **remote**.


- You choice for **--nodetype** and **--mastersalt-nodetype** is certainly one of **server**, **vm**, **vagrantvm** or **devhost**.

    - The default is **server**.
    - **vm** matches a VM (not baremetal)
    - If you choose **devhost**, this mark the machine as a development machine enabling states to act on that, by example installation of a test local-loop mailer.
    - If you choose **vagrantvmt**, this mark the machine as a vagrant virtualbox.
    - If nothing is selected, an appropriate nodetype will be chosen for you
      (example: lcxcontainer on lxc)


- For configuring all salt daemons, you have some extra parameters (here are the environment variables, but you have also
  command line switches to set them

    - **\-\-salt-master-dns**; hostname (FQDN) of the linked master
    - **\-\-salt-master-port**: port of the linked master
    - **\-\-mastersalt**: is the mastersalt hostname (FQDN) to link to
    - **\-\-mastersalt-master-port**: overrides the port for the distant mastersalt server which is 4606 usually (read the script)


Pre installed environments
--------------------------
If you plan to install makina-states, your best bet will be to use a pre backed environment.
For now, we provide a lxc template based on the current LTS ubuntu release.

You can read more here to start play with makina-states.

Usage
-----
boot-salt.sh will try to remember how you configured makina-states.
It stores configs in :

    - /etc/mastersalt/makina-states
    - /etc/salt/makina-states
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

    ./boot-salt.sh --mastersalt <MASTERSALT_FQDN> [--ùastersaltsalt-master-port "PORT OF MASTER  IF NOT 4506"]

If you want to install salt on a bare server, without mastersalt::

    ./boot-salt.sh --no-mastersalt

If you want to install salt on a machine flaggued as a devhost (server + dev mode)::

    ./boot-salt.sh --n devhost

If you want to install and test test mastersalt system locally to your box:

    ./boot-salt.sh --mastersalt-master --mastersalt $(hostname -f)

Useful switches
~~~~~~~~~~~~~~~~

To skip the automatic code update/upgrade::

    ./boot-salt.sh -S

To switch on a makina-states branch, like the **stable** branch in production::

    ./boot-salt.sh -b stable

If it suceeds to find enougth information (nodetype, salt installs, branch), it will automaticly guess the parameters by it self.
In other words, you will just have to type **boot-salt.sh** and verify settings next time you ll use it.

Upgrade
~~~~~~~~
Upgrade will:

    - run predefined & scheduled upgrade code
    - update makina-states repositories in /srv/salt & /srv/makina-states
    - update core repositories (like salt code source in /srv/makina-states/src/salt)
    - redo the daemon configuration if necessary
    - redo the daemon association if necessary
    - do the highstates (salt and masterone if any)
::

    boot-salt.sh -C --upgrade
