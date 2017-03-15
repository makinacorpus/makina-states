---
title: Layout
tags: [topics, ansible]
weight: 900
menu:
  main:
    parent: reference
    identifier: reference_layout
---

## Layout
- Relative to the top ``makina-states`` clone folder.

<pre>
 bin/ansible                    -> wrapper to ansible
 bin/ansible-galaxy             -> wrapper to ansible-galaxy
 bin/ansible-playbook           -> wrapper to ansible-playbook
 bin/salt-call                  -> wrapper to salt-call
 ansible/                       -> ansible plays, roles, modules & etc
 etc/                           -> configuration
   etc/ansible/                 -> ansible configuration
   etc/salt/                    -> saltstack configuration
   etc/makina-states/           -> makina-states  configuration
 pillar/                        -> saltstack pillar files
     pillar/pillar.d/           -> saltstack pillar files (global)
     pillar/private.pillar.d/   -> saltstack pillar files
                                  (for the current node)
     pillar/<$minion>.pillar.d/ -> saltstack pillar files
                                  (for a specific minion)
 salt/makina-states/            -> saltstack states
   makina-states/               -> makina-states saltstack states
   salt/_modules/               -> custom salt modules
   salt/_pillar/                -> custom extpillar modules
</pre>

## Salt pillar
- Saltstack configuration is based on pillars.
- To facilitate configuration of the Top file, we added those features:
    - Any **JSON** file can be used as pillar data.
    - Any **SLS/json** file dropped inside `pillar/pillars.d/` will be loaded for all minion as pillar data
    - Any **SLS/json** file dropped inside `pillar/private.pillars.d` will be only loaded for the current node of operation.
    - Any **SLS/json** file dropped inside `pillar/<$minionid>.pillars.d` will be only loaded for the "\$minionid" host

## Salt + Ansible bridge notes
- Makina-states has better to use an [ansible dynamic inventory](https://github.com/makinacorpus/makina-states/blob/v2/ansible/inventories/makinastates.py)
that bridges the salt pillar with ansible via a salt module:
[mc\_remote\_plllar](https://github.com/makinacorpus/makina-states/blob/v2/mc_states/modules/mc_remote_pillar.py).

- This module is pluggable and will search in the salt modules installed
  those who have declared special named functions:

    ``get_masterless_makinastates_hosts()``
    :   return a list of host to manage

    ``get_masterless_makinastates_groups(minionid, pillar)``
    :   return a list of groups for the specific minion id

- For each host found by all ``get_masterless_makinastates_hosts`` functions:
    -   Get its pillar by calling
        ``mc_remote_pillar.get_pillar($host)``
    -   Extract/generate from informations in the pillar relevant ansible
        host vars for this minion. **saltpillar** ansible hostvar is the
        pillar of this minion.
    -   Generate ansible groups from those hostvars by calling eac
        ``get_masterless_makinastates_groups`` function

- By default, we use the ``mc_pillar`` ext pillar which loads a file:
  ``etc/makina-states/database.sls`` which describe our infractructure and
  this will:
    - list all nodes that are configured as ansible targets
    - generate pillar info for all nodes (and per se fall inside
      the ansible inventory of those related hosts.

## Custom extpillar
- In other words, to add your custom way of managing your hosts:
    - Create an ext\_pillar to complete the pillar for a specific minion
      depending on its ``minion id`` and that's why the easiest way
      is to adopt a minionid/hostname naming scheme.
    - Create a module that implement the ``get_masterless_makinastates_hosts`` && ``get_masterless_makinastates_groups`` functions
    - register the pillar and module to the local makina-states installation (see bellow)
- Take example on:
    - [module](https://github.com/makinacorpus/makina-states/blob/v2/mc_states/modules/mc_pillar.py) : (search for ``get_masterless_makinastates_groups`` && ``get_masterless_makinastates_hosts``
    - [extpillar](https://github.com/makinacorpus/makina-states/blob/v2/mc_states/pillar/mc_pillar.py)

- To load your extpillar, you ll have to add it to the local salt configuration. <br/>
  You can add a file this way

    ```yaml
    $WC/etc/salt/minion.d/99_extpillar.conf 
        ext_pillar:
            - mc_pillar: {}
            - mc_pillar_jsons: {}
            - mycustompillar: {}
    ```

- To load your custom module, place it under `$WC/salt/_modules`
- To load your custom pillar, place it under `$WC/salt/_pillar`

## Verify the pillar for a minion
- Use this command:

    ```sh
    bin/salt-call mc_remote_pillar.get_pillar <minion_id>
    ```

## Verify the groups for a minion
- Use this command:

    ```sh
    bin/salt-call mc_remote_pillar.get_groups <minion_id>
    ```

## (OPTIONAL) Add a cron to speed up pillar generation
- To generate regularly the cron for all the configured minion, to speed
  up regular ansible calls (the pillar will already be cached at the call
  time), you can register a cron that does that.
- ``/etc/cron.d/refresh_ansible``

    <pre>
    15,30,45,00 * * * * root /srv/makina-states/_scripts/refresh_makinastates_pillar.sh
    </pre>
