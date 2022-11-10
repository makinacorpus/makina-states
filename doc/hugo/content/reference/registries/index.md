---
title: Registries & Configuration
tags: [reference, installation]
weight: 1000
menu:
  main:
    parent: reference
---

- We needed a way, in our **salt** states:
    - To deduplicate the cumbersome handling of variables
    - To make cleaner jinja code
    - For a configuration knob, aggregate values from difference sources, by precedence.
- For this, we decided to abstract this in python code
- So, a **registry** in the Makina-States vocabulary is a
  [salt execution module](https://docs.saltstack.com/en/latest/ref/modules/) that returns a python dictionnary:
  - containing various configuration knobs
  - with **sane defaults**
  - overridable at will by the user via the **pillar** or the **grains**.

- The idea was then to use dedicated saltstack execution modules to provide
  a way to have dictionnaries of data aggregated with this precedence:
    - Pillar (**__pillar__**)
    - Grains (**__grains__**)
    - Configuration of the minion (**__opts__**)
    - Configuration of the minion (**__opts__['master]']**)
    - Exemples:
        - [mc_apache](https://github.com/makinacorpus/makina-states/blob/v3/mc_states/modules/mc_apache.py)
        - [mc_nginx](https://github.com/makinacorpus/makina-states/blob/v3/mc_states/modules/mc_nginx.py)
        - [mc_mysql](https://github.com/makinacorpus/makina-states/blob/v3/mc_states/modules/mc_mysql.py)
    - Those registries rely on an heavily used function [``mc_utils.default``](https://github.com/makinacorpus/makina-states/blob/v3/mc_states/modules/mc_utils.py#L681) that will do the job of gathering for the ``configuration prefix`` all the knobs
    from the various pieces of data we want (pillar, grains, opts)

- Thus, by example, you want to install the mysql service:<br>
  You will use this sls:

      ```sh
      bin/salt-call -linfo --retcode-passthrough \
        state.sls makina-states.servies.db.mysql
      ```
- Reading the code of [mysql formula](https://github.com/makinacorpus/makina-states/blob/v3/salt/makina-states/services/db/mysql/configuration.sls#L11), you see that it calls [mc_mysql](https://github.com/makinacorpus/makina-states/blob/v3/mc_states/modules/mc_mysql.py#L157)
    - To override the ``port`` (default: 3306), you can do this in the pillar
      or the grains those ways

     - Flat Method(preferred): **pillar/pillar.d/mysql.sls**

         ```yaml
         makina-states.services.db.mysql.port: 3306
         ```

     - Nested Method: **pillar/pillar.d/mysql.sls**

         ```yaml
         makina-states.services.db.mysql:
            port: 3306
         ```






