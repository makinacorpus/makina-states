Circus configuration
====================

Circus_ is a Python program which can be used to monitor and control processes and sockets.

.. _Circus: https://circus.readthedocs.io/en/latest/

Exposed Hooks:
  circus-pre-restart
    before circusd restart
  circus-post-restart
    after circusd restart

Pillar value start with makina-states.services.monitoring.circus:

    location 
      Edit the directory in which circus is installed. (**locs['apps_dir'] + '/etherpad'**)




