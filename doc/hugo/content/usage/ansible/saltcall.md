---
title: Ansible saltcall module
tags: [topics, ansible]
weight: 300
menu:
  main:
    parent: usage_ansible
---

saltcall Wrapper
----------------
We developped a [special
module](https://github.com/makinacorpus/makina-states/blob/v2/ansible/library/saltcall.py)
to call saltcall on remote systems.

- You can use it via ansible:

    ```sh
    ANSIBLE_TARGETS=$(hostname) bin/ansible all \
      -m saltcall -a "function=test.ping"
    ```

    ```sh
    ANSIBLE_TARGETS=$(hostname) bin/ansible all \
      -m saltcall -a "function=grains.get args=fqdn"
    ```

- Or via a playbook like in [our saltcall one](https://github.com/makinacorpus/makina-states/blob/v2/ansible/plays/saltcall.yml) , usable this way:

    ```sh
    ANSIBLE_TARGETS=$(hostname) bin/ansible-playbook \
     ansible/plays/saltcall.yml -m saltcall -a "function=test.ping"
    ```

It's better to use the playbook because it call the makinastates\_pillar
role to copy locally on the remote box the pillar computed by the
salt+pillar bridge before executing the salt command.
