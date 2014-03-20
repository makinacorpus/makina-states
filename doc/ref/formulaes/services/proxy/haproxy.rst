Postfix
========
Configure haproxy, see the salt :ref:`module_mc_haproxy` module to know which option to configure in pillar.
There are shortcut modes to ease the configuration, please see bellow

Relay mode
-----------

Example pillar use

.. code-block:: yaml

    makina-states.services.proxy.haproxy: true


Local Delivery mode
--------------------
- This will store all mails emitted by local network interfaces locally into the
  configurated recipient mailbox (configured in pillar)

Example pillar use

.. code-block:: yaml

    makina-states.services.proxy.haproxy: true
    makina-states.services.proxy.haproxy.mode: localdeliveryonly
    makina-states.services.proxy.haproxy.local_dest: vagrant@localhost


Exposed hooks
-----------------
- haproxy-pre-install-hook
- haproxy-post-install-hook
- haproxy-pre-conf-hook
- haproxy-post-conf-hook
- haproxy-pre-restart-hook
- haproxy-post-restart-hook
