Postfix
========
Configure postfix, see the salt :ref:`state_mc_postfix` module to know which option to configure in pillar.
There are shortcut modes to ease the configuration, please see bellow

Relay mode
-----------

- This has no local delivery.
- This will forward all emails to a relay host.
- You can use authenticated smtp.

Example pillar use

.. code-block:: yaml

    makina-states.services.mail.postfix: true
    makina-states.services.mail.postfix.mode: relay
    makina-states.services.mail.postfix.relay_host: smtp.relayprovider.com
    makina-states.services.mail.postfix.relay_port: 587
    makina-states.services.mail.postfix.auth: True
    makina-states.services.mail.postfix.auth_user: foo@relayprovider.com
    makina-states.services.mail.postfix.auth_password: xxxXXXxxxXXx
    makina-states.services.mail.postfix.virtual_map:
        /root@.*/: sysadmin@domain.tld
        /postmaster@.*/:  sysadmin@domain.tld
        /abuse@.*/:  abuse@domain.tld

Local Delivery mode
--------------------
- This will store all mails emitted by local network interfaces locally into the
  configurated recipient mailbox (configured in pillar)

Example pillar use

.. code-block:: yaml

    makina-states.services.mail.postfix: true
    makina-states.services.mail.postfix.mode: localdeliveryonly
    makina-states.services.mail.postfix.local_dest: vagrant@localhost


Custom mode
----------------
- This will let you configure each option of postfix explicitly, no defaults from
  relay or localdelivery will be applied.

Example pillar use

.. code-block:: yaml

    makina-states.services.mail.postfix: true
    makina-states.services.mail.postfix.mode: custom
