Installation of a cluster based on mastersalt
==================================================

Briefing
~~~~~~~~~

Most of mastersalt part is configured via a file: ``/srv/mastersalt/database.sls``.
This is a simple YAML (+jinja) file to describe your infra in a very consive
format.

This file is then read by the ``mc_pillar`` execution module which is called from the
``mc_pillar`` ext_pillar module and assemble pieces of information through
PILLAR entries

IOW, The ext pillar will setup the pillar for mastersalt to help to manage
a whole infractructure:

This covers those parts:

    - CA/SSL certificates generation (on master side)
    - CA/SSL certificates delivery (on minions)
    - Supervision (icinga)
    - Authorising SSH access to boxes and configure SSH servers
    - Manage auto upgrades via unattended
    - Managing PAM & NSSconfiguration
    - backups (client & master) (based burp)
    - DNS (bind)
    - LDAP (openldap)
    - Baremetal and VM network configuration (this include setuping ip faiover
      aliases on baremetal servers)
    - Firewall configuration (`ms_iptables <https://github.com/makinacorpus/makina-states/blob/master/files/usr/bin/ms_iptables.py>`_ (simple iptables frontend configured
      via json))
    - repositories managment (APT)
    - locales managment
    - Cloud Controller orchestration

        - Manage dns entries
        - Reverse proxies (haproxy & firewalld (http(s)/ssh/snmp)
        - Spawning VMS (kvm, lxc) and managing their lifecycle

    - Kernel sysctl managment
    - Configure base machine configurations (editors, base packages & so on)
    - etc.

The yaml files doesnt exist at first, you have to create it.
You can get a sample from https://github.com/makinacorpus/makina-states/blob/stable/files/database.sls and adapt it to your needs.
An empty file is generated for you on first install.


Install a mastersalt master
+++++++++++++++++++++++++++
Ensure that your local box FQDN is correctly configured by issuing:

    hostname -f

You should have something like that in your /etc/hosts::

    127.0.0.1 mastersaltmaster.foo.net mastersaltmaster localhost

Then, you can proceed by bootstrapping mastersalt
::

    mkdir -p /srv/mastersalt
    apt-get install -y curl git
    git clone https://github.com/makinacorpus/makina-states.git /srv/mastersalt/makina-states
    /srv/mastersalt/makina-states/_scripts/boot-salt.sh --mastersalt-master --mastersalt $(hostname -f)

After installation you can begin to edit **/srv/mastersalt-pillar/database.sls** and
bring up the rest of your new saltstack based infra, piece after piece !::

    vim /srv/mastersalt-pillar/database.sls

**WARNING** The mastersalt binaries are prefixed with 'master' like:
'mastersalt', 'mastersalt-call', 'mastersalt-run', 'mastersalt-key'.
