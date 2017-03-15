---
title: Ansible
tags: [usage, ansible]
weight: 400
menu:
  main:
    parent: usage
    identifier: usage_ansible
---

## Leaving localhost
- When you want to execute saltstack states (makina-states) remotly,<br>
  here is the prefligh list to do:
    - declare your host in the ``database.sls``
    - Ensure that the target is reachable from ansible
    - Bootstrap makina-states on the remote box, via the providen makinastates role

## Ansible wrappers specifics
- To use ansible, please use makina-states wrappers and <br/>
  <b>never EVER</b> the ansible original scripts directly.<br/>
- If you are using the database.sls, we use ***environment variables*** that are specific to makina-states and
  tell the ext pillar (local saltstack side) for which environment to gather information for.

    ``ANSIBLE_TARGETS``
        : list of hosts that we will act on. this will limit the scope of
          the ext pillars generation thus you have to set it to speed
          up operations.
    ``ANSIBLE_NOLIMIT``
        : if set, we wont limit the scope of ansible to ANSIBLE\_TARGETS

###  Examples
- exemple 1

    ```sh
    ANSIBLE_TARGETS=$(hostname) bin/ansible all -m ping
    ```

- exemple 2

    ```sh
    bin/ansible -c local -i "localhost," all -m ping
    ```

### Examples with salt
- Call a state.sls run

    ```sh
    ANSIBLE_TARGETS=$(hostname) bin/ansible all -m shell \
        -a salt-call --retcode-passthrough state.sls foobar
    ```

### Details
- See:
    - [bin/ansible](https://github.com/makinacorpus/makina-states/blob/v2/_scripts/ansible)
    - [bin/ansible-galaxy](https://github.com/makinacorpus/makina-states/blob/v2/_scripts/ansible-galaxy)
    - [bin/ansible-playbook](https://github.com/makinacorpus/makina-states/blob/v2/_scripts/ansible-playbook)
    - [bin/ansible-wrapper-common](https://github.com/makinacorpus/makina-states/blob/v2/_scripts/ansible-wrapper-common)

- We preconfigure in our wrappers a lot of things like:
    - Loading configuration (roles, playbooks, inventories, plugins) from:
      - ``./``
      - ``./ansible``
      - ``./.ansible``
      - ``<makinastates_install_dir>/ansible``
      -  ``/usr/share/ansible`` (depends of the opt, respects the ansible default configuration)
      - ``/etc/ansible`` (depends of the opt, respects the ansible default configuration)
    - When ``ANSIBLE_TARGETS`` are set, we will limit the play to them
      unless ``ANSIBLE_NOLIMIT`` is set.


## Calling makina-states's flavored  ansible from another repository
As said previously, we load the current folder (and ./.ansible,
./ansible as well).<br/>
This clever trick will let you can add roles and plays to a specific
repository but also be able to depend on plugins or roles defined in makina-states.<br/>
This mean that you ll be able to call the ansible wrapper FROM your directory where
you have your specific ansible installation and the whole will assemble nicely.

- For example:
    - if makina-states is installed in ``/srv/makina-states``
    - your project is installed inside ``/srv/projects/foo/project``
    - You can create your roles inside ``/srv/projects/foo/project/ansible/roles``
    - You can make dependencies of any [makina-states roles](https://github.com/makinacorpus/makina-states/tree/v2/ansible/roles) specially ``makinastates_pillar`` that
      deploy the locally gather pillar for a box to the remote if you are
      not acting on ``localhost``.
    - You ll have to call ``ansible`` or ``ansible-playbook``, do it this way:

        ```sh
        cd /srv/projects/foo/project
        /srv/makina-states/bin/{ansible,ansible-playbook} $args
        ```

## Related
- [salt call module](saltcall)

