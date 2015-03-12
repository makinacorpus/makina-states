Installation & basic usage
==========================
Briefing
----------
To install our base salt installation, just run the boot-salt.sh script as **root**,
please read next paragraphs before running any command.

- All our production installs run 2 instances of salt: **mastersalt** and **salt**
- You will nearly never have to handle much with the **mastersalt** part uness you also use the **cloudcontroller** part as an admin.
- The two instances will have to know where they run to first make the system ready for them.
- All the behavior of the script is controlled via environment variables or command line arguments switches.
- That's why you will need to tell which daemons you want (minion/master) and on what kind of machine you are installing on (vm/vagrant/baremetal).

- The default installed **controller** flavor is **salt**, and in other words, we do not install **mastersalt** by default. ou can tell to install only a minion with using **--no-salt-master**.

- You'll also have to set the **minion id**. The default choice for **--minion-id** is the current machine hostname
  but you can force it to set a specific minion id.

- You choice for **--nodetype** and **--mastersalt-nodetype** is certainly one of **server**, **vm**, **vagrantvm** or **devhost**.

    - The default is **server**.
    - **vm** matches a VM (not baremetal)
    - If you choose **devhost**, this mark the machine as a development machine enabling states to act on that, by example installation of a test local-loop mailer.
    - If you choose **vagrantvmt**, this mark the machine as a vagrant virtualbox.


- For salt, you have some extra parameters (here are the environment variables, but you have also
  command line switches to set them

    - **\-\-salt-master-dns**; hostname (FQDN) of the linked master
    - **\-\-salt-master-port**: port of the linked master
    - **\-\-mastersalt**: is the mastersalt hostname (FQDN) to link to
    - **\-\-mastersalt-master-port**: overrides the port for the distant mastersalt server which is 4606 usually (read the script)


For developers
---------------
If you plan to install makina-states on your local boxes, you do not need to install it directly.
Please and only install & use the `Makina VMS virtualmachine`_.
On this virtual machine, makina-states is pre installed and ready for use.

..  _`Makina VMS virtualmachine`: https://github.com/makinacorpus/vms

Usage
-----
Download
~~~~~~~~~
Get the script::

    wget http://raw.github.com/makinacorpus/makina-states/master/_scripts/boot-salt.sh

Short overview::

    ./boot-salt.sh --help

Detailed overview::

    ./boot-salt.sh --long-help

Install
~~~~~~~~~~

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

    ./boot-salt.sh -b stable

SUMUP Examples
~~~~~~~~~~~~~~~

    - To install on a server (default env=server, default boot=salt_master)::

        ./boot-salt.sh

    - To install on a dev machine (env=devhost, default boot=salt_master)::

        ./boot-salt.sh -n devhost

    - To install on a server and use mastersalt::

        ./boot-salt.sh -b stable --mastersalt mastersalt.makina-corpus.net

boot-salt.sh will try remember to remember how you configured makina-states.
If it suceeds to find enougth information (nodetype, salt installs, branch), it will automaticly guess the parameters by it self.
In other words, you will just have to type **boot-salt.sh** and verify settings next time you ll use it.

Upgrade
~~~~~~~~
Upgrade will:

    - run predefined & scheduled upgrade code
    - update makina-states repository in /srv/salt & /srv/makina-states
    - update core repositories (like salt code source in /srv/makina-states/src/salt)
    - redo the daemon configuration if necessary
    - redo the daemon association if necessary
    - do the highstates (salt and masterone if any)

::

    boot-salt.sh -C --upgrade



