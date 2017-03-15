Ansible related configuration
===============================

Ansible wrappers specifics
----------------------------
To use ansible, please use makina-states wrappers and never
the ansible original scripts directly.

see:

    - `bin/ansible <https://github.com/makinacorpus/makina-states/blob/v2/_scripts/ansible>`_
    - `bin/ansible-galaxy  <https://github.com/makinacorpus/makina-states/blob/v2/_scripts/ansible-galaxy>`_
    - `bin/ansible-playbook  <https://github.com/makinacorpus/makina-states/blob/v2/_scripts/ansible-playbook>`_
    - `bin/ansible-wrapper-common  <https://github.com/makinacorpus/makina-states/blob/v2/_scripts/ansible-wrapper-common>`_

We preconfigure in our wrappers a lot of things like:

    - Loading configuration (roles, playbooks, inventories, plugins) from:

      - ./
      - ./ansible
      - ./.ansible
      - <makinastates_install_dir>/ansible
      - /usr/share/ansible (depends of the opt, respects the ansible default configuration)
      - /etc/ansible (depends of the opt, respects the ansible default configuration)

    - When **ANSIBLE_TARGETS** are set, we will limit the play to them unless
      **ANSIBLE_NOLIMIT** is set.

Indeed, we use environment variables that are specific to makina-states:

    ANSIBLE_TARGETS
        list of hosts that we will act on.
        this will limit the scope of the ext pillars generation
        thus you have to set it to speed up operations.
    ANSIBLE_NOLIMIT
        if set, we wont limit the scope of ansible to ANSIBLE_TARGETS


Examples
---------
::

    ANSIBLE_TARGETS=$(hostname) bin/ansible all -m ping

::

    bin/ansible -c local -i "localhost," all -m ping

Calling makina-states ansible from another repostory
-------------------------------------------------------
As said previously, we load the current folder (and ./.ansible, ./ansible as
well), thus you can add roles and plays and to a specific repository but also
depend on plugins or roles defined in makina-states. Then you ll have to call
the ansible wrapper FROM your directory where you have your specific ansible
installation for them to be usable

For example

    - if makina-states is installed in /srv/makina-states
    - your project is installed inside /srv/projects/foo/project

- You can create your roles inside /srv/projects/foo/project/ansible/roles
- You can make dependencies of any
  `makina-states roles <https://github.com/makinacorpus/makina-states/tree/v2/ansible/roles>`_
  specially **makinastates_pillar**.
- To call ansible, do it this way::

    cd /srv/projects/foo/project
    /srv/makina-states/bin/{ansible,ansible-playbook} $args

saltcall Wrapper
------------------
We developped a `special module <https://github.com/makinacorpus/makina-states/blob/v2/ansible/library/saltcall.py>`_ to call saltcall on remote systems.

You can use it via ansible::

    ANSIBLE_TARGETS=$(hostname) bin/ansible all \
      -m saltcall -a "function=test.ping"
    ANSIBLE_TARGETS=$(hostname) bin/ansible all \
      -m saltcall -a "function=grains.get args=fqdn"

Or via a playbook like in
`our saltcall one <https://github.com/makinacorpus/makina-states/blob/v2/ansible/plays/saltcall.yml>`_
, usable this way::

   ANSIBLE_TARGETS=$(hostname) bin/ansible-playbook \
    ansible/plays/saltcall.yml -m saltcall -a "function=test.ping"

It's better to use the playbook because it call the makinastates_pillar role to
copy locally on the remote box the pillar computed by the salt+pillar bridge
before executing the salt command.
