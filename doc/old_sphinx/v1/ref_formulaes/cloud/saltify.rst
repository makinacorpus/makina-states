Baremetal (via ssh) provision aka salt/saltify
=================================================

As always, the configuration is done via a registry: :ref:`module_mc_cloud_saltify`.

This will ssh to the distant box, transfer and run  boot-salt.sh (makina-states bootstrap),
then install a (master)salt minion and reattach that distant box with the
providen id to this salt master.

IOW, We attach distant boxes with the saltify salt-cloud driver.
For this, we need to:

    - indicate the ssh_host user & passwords
    - indicate which profile to use (minion or mastersalt minion)
    - Maybe indicate a gateway to each the host to attach

* The following modes:

  :salt (default): Attach the linked box as a salt minion only
  :mastersalt: Attach the linked box as a masteralt minion.
               This will also install on it a saltmaster/minion couple.

* You can specify the makina-states branch to use with:

   :bootsalt_branch: branch name

The idea is to add to your specific minion pillar some salty entries as follow:

.. code-block:: yaml

  # minion id to set and also nick fqdn is after "targets."
  makina-states.cloud.saltify.targets.gfoobar.test.com:
    ssh_username: ubuntu
    sudo_password: ubuntu
    password: ubuntu
    ssh_host: 10.5.10.16
    sudo: True
    master: 10.5.0.1 (default to grains['fqdn'])
    master_port: 4506 (default to 4506 or 4606 in mastersalt mode)
  makina-states.cloud.saltify.targets.gfoobar2.test.com:
    ssh_host: 10.5.10.15
    mode: mastersalt
    ssh_username: ubuntu
    password: ubuntu
    sudo_password: ubuntu
    branch: stable
    sudo: True
    master: 10.5.0.1
    master_port: 4506

You can even use a ssh gateway to initiate an host behind a firewall:

.. code-block:: yaml

    ssh_gateway: foo
    ssh_key: /tmp/id_dsa


To activate the driver you need to install the generic & the saltify formulaes

.. code-block:: yaml

    makina-states.cloud.generic: true
    makina-states.cloud.saltify: true




