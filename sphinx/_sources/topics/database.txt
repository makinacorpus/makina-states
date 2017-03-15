Minions managment via database.sls
====================================
We use a special file: **$WC/etc/makina-states/database.sls**.
for describing our infractrusture and specially how to
access to the remote systems.

At first, you will need to copy **$WC/etc/makina-states/database.sls.in**
which is a sample, and adapt it to your needs::

    cp etc/makina-states/database.sls.in \
          etc/makina-states/database.sls
    $EDITOR etc/makina-states/database.sls

The contents of the file is mostly self explainatory.

This file is then parsed by the mc_pillar module (called via an extpillar hook)
to get the appropriate pillar for a specific minion id that represant a good
part of its system configuration from backups to ssl, to cloud configuration and
so on.

We heavyly rely on memcached to improve the performance, so first please
install it this way::

    bin/salt-call -lall state.sls makina-states.services.cache.memcached

Verify the pillar for a minion after a database.sls change
--------------------------------------------------------------
Use this command::

  service memcached restart
  bin/salt-call mc_pillar.ext_pillar <minion_id>

