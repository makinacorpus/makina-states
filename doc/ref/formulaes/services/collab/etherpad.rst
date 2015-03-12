Etherpad configuration
======================

Etherpad_ allows you to edit documents collaboratively in real-time, much like a
live multi-player editor that runs in your browser.

.. _Etherpad: http://etherpad.org/

It uses circus to monitor the process.

Pillar
------

Pillar values start with makina-states.services.collab.etherpad:

==============  ================================================  ==============================
Value           Description                                       Default
==============  ================================================  ==============================
version         Change which version of etherpad is installed.    '1.3.0'
location        Edit the directory in which circus is installed.  locs['apps_dir'] + '/etherpad'
apikey          The secret used to encrypt transmissions.         'SECRET-API-KEY-PLS-CHANGE-ME'
title           The title of the server.                          'Etherpad'
ip              Ip on which the server will bind.                 '0.0.0.0'
port            Port the server will listen for.                  '9001'
dbType          Type of the database.                             'dirty'
dbSettings      Settings of the database.                         '{"filename": "var/dirty.db"}'
requireSession  Require session setting.                          'true'
editOnly        Edit only setting.                                'false'
admin           Create an admin or not.                           False
adminPassword   Admin's password.                                 'admin'
==============  ================================================  ==============================


