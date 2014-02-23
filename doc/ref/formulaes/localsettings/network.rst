Network configuration
=====================
Configure machine physical network based on pillar information.
This state will only apply if you set to true the config value (grain or pillar): **makina-states.localsettings.network_managed**
The template is shared with the lxc state, please also look at it.

Exposed settings:

    :makina-states.localsettings.network.managed: default: False

It will look for extra pillar entries suffixed in **-makina-network** as follow

.. code-block:: yaml

    *-makina-network:
      ifname:
      - auto: opt (default: True)
      - mode: opt (default: dhcp or static if address)
      - address: opt
      - netmask: opt
      - gateway: opt
      - dnsservers: opt

EG

.. code-block:: yaml

    makina-states.localsettings.network.managed : true
    myhost-makina-network:
      etho: # manually configured interface
        - address: 8.1.5.4
        - netmask: 255.255.255.0
        - gateway: 8.1.5.1
        - dnsservers: 8.8.8.8
      em1: {} # -> dhcp based interface

