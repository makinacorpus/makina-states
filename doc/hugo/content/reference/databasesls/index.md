---
title: database.sls
tags: [topics, minions, databasesls]
weight: 900
menu:
  main:
    parent: reference
    identifier: reference_databasesls
---

- For configuring a single machine, you can rely on a local crafted pillar,
  but to operate on a cluster, it would be a lot more cumbersome and not **DRY**.
- Fir this we created [``mc_pillar``](https://github.com/makinacorpus/makina-states/blob/v2/mc_states/modules/mc_pillar.py), an ext_pillar that describe a whole
  cluster infrastructure from a single **SLS** file.
- This special file, [``etc/makina-states/database.sls``](https://github.com/makinacorpus/makina-states/blob/v2/etc/makina-states/database.sls.in). will
  describe our infrastructure and specially how to access to the remote
  systems.
- At first, you will need to copy ``etc/makina-states/database.sls.in`` which is a sample, and adapt it to your needs:

    ```sh
    cp etc/makina-states/database.sls.in \
          etc/makina-states/database.sls
    $EDITOR etc/makina-states/database.sls
```

    - The contents of the file is mostly self explainatory.

- This file is then parsed by the **mc\_pillar module** (called via an
  extpillar hook) to get the appropriate pillar for a specific minion id.
  This pillar aims to grab a good part of its system configuration from backups to
  ssl, to cloud configuration and so on.
- We heavyly rely on memcached to improve the performance, so first please
  install it this way:

    ```sh
    bin/salt-call -lall state.sls makina-states.services.cache.memcached
    ```

Verify the pillar for a minion after a database.sls change
----------------------------------------------------------

- Use this command:

    ```sh
    service memcached restart
    bin/salt-call mc_pillar.ext_pillar <minion_id>
    ```
