Shorewall configuration
========================
Configure shorewall, see the following documentation + salt :ref:`module_mc_shorewall` module to know which option to configure in pillar.

The firewall is able to mostly autoconfigire itsel, even for rpn, lxc & docker; you
should just only have rules or params to add !

For tricky part, you can fallback on configuration hints via pillar/grains.

By default we configure a firewall enabling ssh, mail and and http(s) services
only.

There are variables to easily restrict access by ip.

Default Rules
--------------
We create defaults rules for you:

    - fw -> all defined zones: allowed
    - allow docker zone from/to all internal subnets
    - allow lxc zone to {docker, fw} but no inter lxc
    - drop all other traffic by default
    - enable smtp, dns, ssh, http
    - disable invalid, ping & ftp

You can either:

    - disable all the default rules
    - disable or enable the traffic controlled by one of those network flows

Enable/disable default rules
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Allowed by default:

    makina-states.services.firewall.shorewall.no_default_rules
        true/false (false)
    makina-states.services.firewall.shorewall.no_dns
        true/false (false)
    makina-states.services.firewall.shorewall.no_web
        true/false (false)
    makina-states.services.firewall.shorewall.no_ssh
        true/false (false)
    makina-states.services.firewall.shorewall.no_ping
        true/false (false)
    makina-states.services.firewall.shorewall.no_mastersalt
        true/false (false)
    makina-states.services.firewall.shorewall.no_ntp
        true/false (false)
    makina-states.services.firewall.shorewall.no_burp
        true/false (false)
    makina-states.services.firewall.shorewall.no_ldap
        true/false (false)
    makina-states.services.firewall.shorewall.no_mumble
        true/false (false)

Restricted to localhost by default:

    makina-states.services.firewall.shorewall.no_syslog
        true/false (false)

Blocked by default:

    makina-states.services.firewall.shorewall.no_salt
        true/false (true)
    makina-states.services.firewall.shorewall.no_invalid
        true/false (true)
    makina-states.services.firewall.shorewall.no_snmp
        true/false (true)
    makina-states.services.firewall.shorewall.no_postgresql
        true/false (true)
    makina-states.services.firewall.shorewall.no_mysql
        true/false (true)
    makina-states.services.firewall.shorewall.no_ftp
        true/false (true)

Restrict access for some services
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Just configure a **RESTRICTED_SERVICE** parameter !
Supported params are:

    - **RESTRICTED_SSH**: for restricting ssh access
    - **RESTRICTED_SNMP**: for restricting snmp access
    - **RESTRICTED_PING**: for restricting snmp access
    - **RESTRICTED_FTP**: for restricting ftp access
    - **RESTRICTED_POSTGRESQL**: for restricting postgres access
    - **RESTRICTED_MYSQL**: for restricting mysql access
    - **RESTRICTED_SYSLOG** for restricting syslog access
    - **RESTRICTED_NTP** for restricting syslog access
    - **RESTRICTED_MUMBLE** for restricting syslog access
    - **RESTRICTED_LDAP** for restricting syslog access
    - **RESTRICTED_BURP** for restricting syslog access

.. code-block:: yaml

    makina-states.services.firewall.shorewall.params.RESTRICTED_SSH: "<src_def>"

EG:

.. code-block:: yaml

    makina-states.services.firewall.shorewall.params:
      IP_FOO: "12.232.243.200"
      IP_COMPANY: "12.23.9.8,2.24.3.18,1.24.19.4"
      IP_SUPERVISION: "19.14.1.0,1.11.3.26"
      RESTRICTED_SSH: "net:$IP_FOO,$IP_COMPANY,$IP_SUPERVISION"
      RESTRICTED_SNMP: "net:$IP_SUPERVISION"
      RESTRICTED_PING: "net:$IP_SUPERVISION"

Firewalling lxc containers
~~~~~~~~~~~~~~~~~~~~~~~~~~
default policy:

    - lxc -> dck: auth
    - dck -> lxc: auth
    - fw -> lxc: auth
    - lxc -> net: auth


Dedibox RPN firewalling
~~~~~~~~~~~~~~~~~~~~~~~
default policy:

    - rpn -> all: drop
    - fw -> rpn: auth

Firewalling docker containers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
default policy:

    - dck -> net: auth
    - dck -> dck: auth
    - lxc -> dck: auth
    - dck -> lxc: auth

Disable firewall even if installed
--------------------------------------
Disable shorewall service to start in config (pillar, grain)

.. code-block:: yaml

  makina-states.services.shorewall.enabled: True | False


Defining shorewall interfaces
------------------------------

.. code-block:: yaml

  makina-states.services.firewall.interfaces:
    shorewall-zone-name:
      - interface: phyname
        options: shorewall interface options (man shorewall-interfaces)

Eg:

.. code-block:: yaml

  makina-states.services.firewall.interfaces:
    net:
      - interface: eth0
        options: tcpflags,dhcp,nosmurfs,routefilter,logmartians,sourceroute=0


Masquerade configuration
-------------------------

.. code-block:: yaml

  makina-states.services.firewall.shorewall.masqs:
    masq: (man shorewall-masq)
      interface-comment:
        interface: ifname
        source: (opt)
        address: (opt)
        proto: (opt)
        ports: (opt)
        ipsec: (opt)
        mark: (opt)

EG:

.. code-block:: yaml

    makina-states.services.firewall.shorewall.masq:
      lxc:
        interface: eth0
        source: lxcbr0

Params configuration
------------------------

Please note:

    - All paramsare automaticly prefixed with **SALT_**
    - All params are **sorted** lexicographically after the loading
    - You needif you reference params to use the **SALT_** prefix, we
      wont replace params automatically.

.. code-block:: yaml

  makina-states.services.firewall.shorewall.params:
    param: value

EG:

.. code-block:: yaml

    makina-states.services.firewall.shorewall.params:
      thishostguest: 10.0.3.2
      00_cd: 10.0.3.2
      00_ab: 10.0.3.2
      a: 1

mapping afterloading:

.. code-block:: yaml

    makina-states.services.firewall.shorewall.params:
      SALT_00_ab: 10.0.3.2
      SALT_00_cd: 10.0.3.2
      SALT_a: 1
      SALT_thishostguest: 10.0.3.2

Zones configuration
--------------------
.. code-block:: yaml

  makina-states.services.firewall.shorewall.zones:
    NAME: (man shorewall-zones)
      type: zone type
      options: (opt)
      in: (opt)
      out: (opt)
      in_options: (opt)
      out_options: (opt)

EG:

.. code-block:: yaml

    makina-states.services.firewall.shorewall.zones:
      zones:
        fw:  {type: firewall}
        net: {type: ipv4}
        lxc: {type: ipv4}

Policy configuration
-------------------------
.. code-block:: yaml

  makina-states.services.firewall.shorewall.policies: (list of dict):
    - source: shorewall zone (man shorewall-policies)
      dest: shorewall zone
      policy: policy
      loglevel: 'loglevel (opt)'
      limit: 'limit:burst (opt)'

EG:

.. code-block:: yaml

    makina-states.services.firewall.shorewall.policies:
      policy:
        - {source: $FW, dest: net, policy: ACCEPT,}
        - {source: rpn, dest: all, policy: DROP, loglevel: info}
        - {source: all, dest: all, policy: REJECT, loglevel: info}

Rules configuration
--------------------------
.. code-block:: yaml

  makina-states.services.firewall.shorewall.rules: (list of dict):
     - section: new (default) : established | related | all (opt)
       action: action todo
       source: source addr     (man shorewall-rules)
       dest: dest addr
       proto: (opt)
       dport: (opt)
       sport: (opt)
       odest: (opt)
       rate: (opt)
       user: (opt)
       mark: (opt)
       connlimit: (opt)
       time: (opt)
       headers: (opt)
       switch: (opt)

EG:

::

    makina-states.services.firewall.shorewall.rules:
      - {section: established, action: 'Invalid(DROP)', source: net, dest: all}
      - {action: Invalid(DROP), source: net, dest: all}
      - {action: DNS(ACCEPT),   source: all, dest: all}
      - {action: SSH(ACCEPT),   source: all, dest: all}
      - {action: Ping(ACCEPT),  source: all, dest: all}
      - {action: Ping(DROP),    source: net, dest: $FW}
      - {comment: 'thishostguest lxc'}
      - {action: DNAT, source: net, dest: 'lxc:${thishostguest}:80', proto: tcp, dport: 8082}
      - {comment: 'dhcp in lxc'}
      - {action: ACCEPT, source: lxc, dest: fw , proto: udp, dport: '67:68'}
      - {action: ACCEPT, source: fw , dest: lxc, proto: udp, dport: '67:68'}
      - {comment: 'salt'}
      - {action: ACCEPT, source: all, dest: fw, proto: 'tcp,udp', dport: '4506,4505'}
      - {comment: 'relay smtp from lxc and drop from net'}
      - {action: Invalid(DROP), source: net, dest: all, proto: 'tcp,udp', dport: 25}
      - {action: ACCEPT       , source: lxc, dest: fw , proto: 'tcp,udp', dport: 25}


Default options
------------------
a lot of options has been duplicated and parsed the same way to have two keys to
facilitate default behavior for firewall + minus variations without having to
deal with macros.

Be aware that we use those 'defaults' to apply/append/update (no override)
also the default firewall configuration if you have not disabled the
autoconfiguration.

Supported defaults:

    - rules (default_rules)
    - zones (default_zones)
    - interface: (default_interfaces)
    - masqs (default_masqs)
    - params (default_params)
    - policies (default_policies)

Example:

firewallcommon.sls::

  makina-states.services.firewall.shorewall.default_rules:
      - {action: Invalid(DROP), source: net, dest: all}

firewall1.sls::

  makina-states.services.firewall.shorewall.rules:
      - {action: WEB(ACCEPT), source: net, dest: all}

firewall2.sls::

  makina-states.services.firewall.shorewall.rules:
      - {action: SSH(ACCEPT), source: net, dest: all}

Don't Repeat Yourself Tips and tricks
---------------------------------------
Use jinja macros !

EG:

**/srv/pillar/firewall-common.sls**
::

    {% macro params %}
        ip1: X.X.X.X
    {% endmacro %}

**/srv/pillar/minionfirewall.sls**
::

    {% import 'firewall-common.sls' as c with context %}
    makina-states.services.firewall.shorewall.params:
        {{c.params()}}
        ip2: Y.Y.Y.Y

.. vim:set ts=2 sts=2:


