Baremetal (via ssh) provision
===================================

As always, the configuration is done via a registry: :ref:`module_mc_saltcloud`.


This will ssh to the distant box, install boot-salt.sh (makina states boostrap),
then install a (master)salt minion and reattach that distant box with the
providen id to this salt master.

IOW, We attach distant boxes with the saltify salt cloud driver.
For this, we need to:

    - indicate the ssh_host user & passwords
    - indicate which profile to use (minion or mastersalt minion)

* The following modes:

  :salt (default): Attach the linked box as a salt minion only
  :mastersalt: Attach the linked box as a masteralt minion.
               This will also install on it a saltmaster/minion couple.

* You can specify the makina-states branch to use with:

   :bootsalt_branch: branch name


The idea is to add to your specific minion pillar some salty entries as follow:

.. code-block:: yaml

  makina-states.services.cloud.salty_targets:
    # minion id to set and also nick fqdn
    gfoobar.test.com:
      ssh_username: ubuntu
      sudo_password: ubuntu
      password: ubuntu
      ssh_host: 10.5.10.16
      sudo: True
      master: 10.5.0.1 (default to grains['fqdn'])
      master_port: 4506 (default to 4506)
    gfoobar2.test.com:
      ssh_host: 10.5.10.15
      mode: mastersalt
      ssh_username: ubuntu
      password: ubuntu
      sudo_password: ubuntu
      branch: stable
      sudo: True
      master: 10.5.0.1
      master_port: 4506

