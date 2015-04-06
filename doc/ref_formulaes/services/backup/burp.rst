burp configuration
========================

see :ref:`module_mc_burp`

Configure a burp server.

Use the makina-states.services.backup.burp.client to :

    - install burp binary
    - install the cron

Use the makina-states.services.backup.burp.server to :

    - install burp binary on server
    - configure server
    - generate client backup configuration files part
    - push & dispatch & restart burp services on clients

- the burp server node must access the client via ssh as root via a key
  without password.
- Server & Clients must have **rsync**.
- The backuped machines must access the burp server on **4971** port.
- We offer a way to access clients via a ssh gateway

Burp uses a 'check for backup timer', each client will have a cron that ask the
server to know if it is time for the client to be backuped, and in this case,
the backup starts from the client.

This is why there is a parameter 'cron_periodicity' which is by default ran each
20 minutes and sprayed all over one hour between clients for the load not to be
high on backup server.

The number of simultaneous backups is controlled via the 'max_children'
server parameter.


