
.. _bind_documentation:

BIND/NAMED integration
======================

**WARNING**
    Bind is used as a cache dns server only right now, we have
    not finnished the zone management.
    So the docuementation about pillar zone management, etc is not fully
    implemented yet (and even deactivated to avoid misconfiguration

Generalities
------------
- On everything else than containers, we:

    - activate bind at least as a cache dns
    - Remove dnsmasq as caching dns

- We separate logs in logical log files
- Me manage the dns zones inside bind views
- you must install bind tools prior to run (or run twice) to have all the tool
  neccessary to genrate tsig infos
- The default view is named **net**
- We can manage
- Idea is
    - You defines zone with rrs
    - You define views
    - for each zone, you feed the views list to link to those
      views

..    - view
..    - master and slave zones
..
..      - /etc/bind/zones
..
..    - reverse master and slave views
..
..      - /etc/bind/reverses

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
        is it a **master** or **slave** zone
    makina-states.services.dns.bind.masters
        For slave zones, list of masters.
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

    name
        optjonnal fqdn of the host, default to the <id> part
        in the pillar string. This is the SOA name.
    template
        If true, we will use a template to generate the zone file, see the
        defaults templates.

    source

        - alternative template file if template if True
        - Otherwise, plain text source file for zone

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
        is it a **master** or **slave** zone
    salves
        For master zones, list of slave servers.
        This is optionnal
    masters
        For slave zones, list of masters.
        This is mandatory

Defaults templates settings
-----------------------------
    makina-states.services.dns.bind.zone_template
        Template to generate zones
    makina-states.services.dns.bind.reverse_template
        Template to generate reverse zones
    makina-states.services.dns.bind.sec_zone_template
        Template to generate slave zones
    makina-states.services.dns.bind.sec_reverse_template
        Template to generate reverse slave zones

Define a new acl
----------------
An acl is in the form

.. code-block:: yaml

    makina-states.services.dns.bind.acls.<name>:
        clients: []

Exemple:

.. code-block:: yaml

    makina-states.services.dns.bind.acls.sec1:
        clients: ['!1.2.4.3']

Edit the client for the default 'local' acl which has recursion enabled

.. code-block:: yaml

    makina-states.services.dns.bind.acls.local.clients:
       clients: ['192.168/16', '127.0.0.1', '::1',]

Define a new server entry
-----------------------------
A server is in the form

.. code-block:: yaml

    makina-states.services.dns.bind.servers.<name>:
        keys: []

Exemple:

.. code-block:: yaml

    makina-states.services.dns.bind.servers.18.2.5.6:
        keys: ['sec1-key']

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
--------------------
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

Manage a zone directly from a file, no generation
----------------------------------------------------
.. code-block:: yaml

    makina-states.services.dns.bind.zones:
      template: false
      source: salt:///srv/salt/myzone

    makina-states.services.dns.bind.zones.foo.net:
      serial: 2
      rrs:
        - '@ IN A 1.2.4.4'
    makina-states.services.dns.bind.zones.foo.loc
      views: [intranet]
      serial: 2
      fqdn: foo.net
      rrs:
        - '@ IN A 192.168.4.4'

Save for reverse zone except the id would be the ip bits.

Manage a slave zone
-----------------------
.. code-block:: yaml

    makina-states.services.dns.bind.slave_zones.foo.net:

Save for reverse zone except the id would be the ip bits.

An example or a master/slave scenario
---------------------------------------
on a shared pillar::

    {% set masterip = '1.2.3.5' %}
    {% set slave1ip = '1.2.3.4' %}
    {% set slave1ip_tsig = salt['mc_bind.tsig_for'](slave1ip) %}
    makina-states.services.dns.bind.keys.{{slave1ip}}:
      algorithm: HMAC-SHA512
      secret: "{{slave1ip_tsig}}"

On the master pillar::

    makina-states.services.dns.bind: true
    include:
        - common
    makina-states.services.dns.bind.zones.toto.loc:
      allow_transfer: ['key "{{slave1ip}}"']
      serial: 4
      rrs:
        - '@ IN A 1.2.4.4'
        - 'ns IN A 1.2.4.4'
        - 'mx IN A 1.2.4.4'
        - '@ IN MX 10 mx.foo.net.'
        - '@ IN NS ns.foo.net.'
    makina-states.services.dns.bind.servers.{{slave1ip}}:
      keys: ["{{slave1ip}}"]

This will enable the master to sign data sent to slave1

On the pillar slave targeted pillar, now::

    makina-states.services.dns.bind: true
    include:
        - common
    makina-states.services.dns.bind.servers.{{masterip}}:
      keys: ["{{slave1ip_tsig}}"]
    makina-states.services.dns.bind.zones.toto.loc:
      server_type: slave
      masters: ["{{masterip}}"]



