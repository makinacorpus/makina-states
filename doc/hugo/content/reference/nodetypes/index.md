---
title: Nodetypes
tags: [reference, installation]
weight: 2000
menu:
  main:
    parent: reference
    identifier: reference_nodetypes
---

### Nodetypes

- Your choice for ``nodetype`` is one of:

     **scratch (default)**
     :   only manage the ansible/salt installation and configuration.<br/>
         You ll want to activate this mode if you want
         to apply explicitly your states without relying of default
         nodetypes configuration.

     **server**
     :   matches a baremetal server, and manage it
         from end to end (base packages, network, locales, sshd, crond,
         logrotate, etc, by default)

     **vm**
     :   VM (not baremetal), this is mostly like **server**

     **lxccontainer**
     :   matches a lxc container mostly like **server**
         but install and fix lxc boot scripts

     **laptop**
     :   mostly like **server** but also install packages for
         working on a developement machine (prebacking a laptop for
         a dev

     **dockercontainer**
     :   matches a VM (not baremetal), this is
         mostly like **server**, but install & preconfigure circus to
         manage daemons.

     **devhost**
     :   development machine enabling
         states to act on that, by example installation of a test
         local-loop mailer.

     **vagrantvm**
     :    flag vagrant boxes and is a subtype of devhost



- You can tell [``boot-salt2.sh``](/usage/) which nodetype to use via the ``--nodetype`` switch

    ```sh
    boot-salt2.sh --nodetype server --reconfigure
    ```

### Switching to another nodetype on an already installed environment
- If you installed the **scratch** preset and want to switch to another preset:

    ```sh
    bin/salt-call state.sls makina-states.nodetypes.<your_new_preset>
    ```

- If you installed a preset and want to switch to another preset:
    - edit ``etc/makina-states/nodetype`` and put your new preset
    - edit ``etc/makina-states/nodetypes.yaml`` and set to false your old preset
    - Ask bootsalt to remember

        ```sh
        boot-salt2.sh --nodetype <your_new_preset> --reconfigure
        ```

    - Finally, run:

        ```sh
        bin/salt-call state.sls makina-states.nodetypes.<your_new_preset>
        ```


