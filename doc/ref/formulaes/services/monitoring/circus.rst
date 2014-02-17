Circus configuration
====================

Circus_ is a Python program which can be used to monitor and control processes and sockets.

.. _Circus: http://circus.readthedocs.org/en/latest/

Pillar
------

Pillar value start with makina-states.services.monitoring.circus:

========   ================================================  ==============================
Value      Description                                       Default
========   ================================================  ==============================
location   Edit the directory in which circus is installed.  locs['apps_dir'] + '/etherpad'
========   ================================================  ==============================

Macros
------

You can use the circusAddWatcher macro to add a watcher:

    circusAddWatcher(name, cmd, args="", extras="")

* name: name of the watcher
* cmd: command to execute and to monitor
* args: arguments for the above command
* extras: extras configuration
