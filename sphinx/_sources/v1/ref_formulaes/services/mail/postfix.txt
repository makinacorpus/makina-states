Postfix
========
Configure postfix, see the salt :ref:`module_mc_postfix` module to know which option to configure in pillar.
There are shortcut modes to ease the configuration, please see bellow

Focus on how you can configure postfix (under the hood, we feed hastables):

    - makina-states.services.postfix.sasl_passwd: /etc/postfix/sasl_passwd mappings
    - makina-states.services.postfix.transport /etc/postfix/transports (useful for relay wildcards)
    - makina-states.services.postfix.relay_domains /etc/postfix/relay domains (hosts)
    - makina-states.services.postfix.mydestinations /etc/postfix/mydestinations
    - makina-states.services.postfix.virtual_map: /etc/postfix/virtual_map (better way of rewriting aliases)

Each of those file has a .local counterpart which lets you put inside manual
configuration. eg: /etc/postfix/transports.local

Relay mode
-----------

- This has no local delivery.
- This will forward all emails to a relay host.
- You can use authenticated smtp.

Example pillar use

.. code-block:: yaml

    makina-states.services.mail.postfix: true

    makina-states.services.mail.postfix.mode: relay
    makina-states.services.mail.postfix.transport:
      - nexthop: relay:[mx.f.com]

    makina-states.services.mail.postfix.auth: true
    makina-states.services.mail.postfix.sasl_passwd:
      - entry '[mx.f.com]'
        user: xxx@f.com
        password: xx

    makina-states.services.mail.postfix.virtual_map:
      /root@.*/: sysadmin@f.com
      /postmaster@.*/: sysadmin@f.com
      /abuse@.*/: abuse@f.com

Local Delivery mode
--------------------
- This will store all outbound mails emitted by local network interfaces locally into the nobody mailbox (/var/spool/nobody/
  configurated recipient mailbox (configured in pillar)

Example pillar use

.. code-block:: yaml

    makina-states.services.mail.postfix: true
    makina-states.services.mail.postfix.mode: localdeliveryonly

Redirect Delivery mode
-----------------------
- This will redirect all outbound mails emitted by local network to a specific address

Example pillar use

.. code-block:: yaml

    makina-states.services.mail.postfix: true
    makina-states.services.mail.postfix.mode: redirect
    makina-states.services.mail.postfix.local_dest: kiorky@gmail.com

If you need to identify yourself to the outbound smtp::

    makina-states.services.mail.postfix: true
    makina-states.services.mail.postfix.mode: redirect
    makina-states.services.mail.postfix.auth: true
    makina-states.services.mail.postfix.local_dest: kiorky@gmail.com
    makina-states.services.mail.postfix.sasl_passwd:
      - entry '[smtp.gmail.com']
        user: kiorky@gmail.com
        password: **

Custom mode
----------------
- This will let you configure each option of postfix explicitly, no defaults from
  relay or localdelivery will be applied.

Example pillar use

.. code-block:: yaml

    makina-states.services.mail.postfix: true
    makina-states.services.mail.postfix.mode: custom


Exposed hooks
-----------------
- postfix-pre-install-hook
- postfix-post-install-hook
- postfix-pre-conf-hook
- postfix-post-conf-hook
- postfix-pre-restart-hook
- postfix-post-restart-hook


