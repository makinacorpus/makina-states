
.. _bind_documentation:

BIND/NAMED integration
======================

Generalities
------------
- On everything else than containers, we:

    - activate bind at least as a cache dns
    - Remove dnsmasq as caching dns

- Me manage the dns zones inside bind views
- The default view is named **net**
- We separate logs in logical log files
- We can manage

    - view
    - primary and secondary zones

      - /etc/bind/zones

    - reverse primary and secondary views

      - /etc/bind/reverses

Hooks
----------
    :bind-pre-install: prefore pkg install
    :bind-post-install: after pkg install
    :bind-pre-conf: before touching to any conf file
    :bind-post-conf: after configuration
    :bind-pre-restart: before service restart
    :bind-post-restart: after service restart
    :bind-pre-reload: before service reload
    :bind-post-reload: after service reload

Registry
----------

For the documentation on usage, please look :ref:`module_mc_bind`.

Defaults SOA settings
-----------------------------

    makina-states.services.dns.bind.ttl
        ttl for SOA record
    makina-states.services.dns.bind.serial
        zone serial
    makina-states.services.dns.bind.refresh
        zone refresh time
    makina-states.services.dns.bind.retry
        zone retry time
    makina-states.services.dns.bind.expire
        zone expire time
    makina-states.services.dns.bind.minimum
        zone minimum
    makina-states.services.dns.bind.notify
        is notify activated in named conf (**True**/**False**)
    makina-states.services.dns.bind.server_type
        is it a **primary** or **secondary** zone
    makina-states.services.dns.bind.masters
        For secondary zones, list of masters.
        This is mandatory


.. _dns_views:

Configured in pillar Zones
--------------------------------------

The scheme to name a new zone is

.. code-block:: yaml

    makina-states.services.dns.bind.<zonekind>.<zonename>:
        setting1: value

You can override default settings on a per zone basis.
Please look at implementation to know all switchs, but here are the fields
inside a zone mapping:

    template
        If true, we will use a template to generate the zone file, see the
        defaults templates.
    source

        - alternative template file if template if True
        - Otherwise, plain text source file for zone

    view
        the view to put the zone in, default to net
    views
        the views to put the zone in, default to [net]
    ttl
        ttl for SOA record
    serial
        zone serial
    refresh
        zone refresh time
    retry
        zone retry time
    expire
        zone expire time
    expire
        zone expire time
    minimum
        zone minimum
    notify
        is notify activated in named conf (**True**/**False**)
    server_type
        is it a **primary** or **secondary** zone
    secondaries
        For primary zones, list of secondary servers.
        This is optionnal
    masters
        For secondary zones, list of masters.
        This is mandatory

Defaults templates settings
-----------------------------
    makina-states.services.dns.bind.zone_template
        Template to generate zones
    makina-states.services.dns.bind.reverse_template
        Template to generate reverse zones
    makina-states.services.dns.bind.sec_zone_template
        Template to generate secondary zones
    makina-states.services.dns.bind.sec_reverse_template
        Template to generate reverse secondary zones

Define a new acl
----------------
An acl is in the form

.. code-block:: yaml

    makina-states.services.dns.bind.servers.<name>:
        keys: []

Exemple:

.. code-block:: yaml

    makina-states.services.dns.bind.servers.18.2.5.6:
        keys: ['sec1-key']


Define a new server entry
-----------------------------
An acl is in the form

.. code-block:: yaml

    makina-states.services.dns.bind.servers.<name>:
        clients: []

Exemple:

.. code-block:: yaml

    makina-states.services.dns.bind.serers.sec1:
        clients: ['!1.2.4.3']


Define a new key
----------------
A key is in the form

.. code-block:: yaml

    makina-states.services.dns.bind.keys.<name>:
      algorithm: hmac-md5 (default to this)
      secret: '<secure data>'

Exemple:

.. code-block:: yaml

    makina-states.services.dns.bind.keys.loc1:
      secret: 'aaaqsfsqfqsdfqsdfqsdfgeZA=='

RNDC configuration
-------------------
The configuration is automatic.

Bits are in:

    - /etc/rndc.conf
    - /etc/rndc.key
    - /etc/bind.conf.key

Define a new view
----------------
A view is in the form
The linking between zones and view is done as a per view basis.
See :ref:`dns_views`.

.. code-block:: yaml

    makina-states.services.dns.bind.views.<name>:
      match_clients: []
      recursion: no
      additional_from_cach: no
      additional_from_auth no

Exemple:

.. code-block:: yaml

    makina-states.services.dns.bind.views.intranet;
      match_clients: ['10.0.0.0/16']
      recursion: yes
      additional_from_cach: no
      additional_from_auth: no

Define inner records (**RRs**)
-------------------------------

Manage a zone directly from a file, no generation
----------------------------------------------------
.. code-block:: yaml

    makina-states.services.dns.bind.zones:
      template: false
      source: file:///srv/salt/myzone

Manage a primary zone
---------------------
.. code-block:: yaml

    makina-states.services.dns.bind.zones.foo.net:

Manage a reverse zone
-----------------------
.. code-block:: yaml

    makina-states.services.dns.bind.rzones.foo.net:

Manage a secondary zone
-----------------------
.. code-block:: yaml

    makina-states.services.dns.bind.secondary_zones.foo.net:

Manage a secondary reverse zone
-------------------------------
.. code-block:: yaml

    makina-states.services.dns.bind.secondary_rzones.foo.net:

