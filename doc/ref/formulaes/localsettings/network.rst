Network configuration
=====================
Configure machine physical network based on pillar information.
This state will only apply if you set to true the config value (grain or pillar): **makina-states.localsettings.network_managed**
The template is shared with the lxc state, please also look at it.

Exposed settings:

    :makina-states.localsettings.network.managed: default: False

It will look for extra pillar entries suffixed in **-makina-network** as follow

.. code-block:: yaml

    makina-states.localsettings.network.interfaces.{{ifname}}:
      auto: opt (default: True)
      mode: opt (default: dhcp or static if address)
      address: opt
      netmask: opt
      gateway: opt
      dnsservers: opt
      pre-up: opt
        - list of rules non prefixed with post-up
      post-up: opt
        - list of rules non prefixed with post-up
      pre-down: opt
        - list of rules non prefixed with pre-down
      post-down: opt
        - list of rules non prefixed with pre-down

EG

.. code-block:: yaml

    makina-states.localsettings.network.managed : true
    # manually configured interface
    makina-states.localsettings.network.interfaces.eth0:
      address: 8.1.5.4
      netmask: 255.255.255.0
      gateway: 8.1.5.1
      dnsservers: 8.8.8.8
    makina-states.localsettings.network.interfaces.em1: {} # -> dhcp based interface
    makina-states.localsettings.network.interfaces.eth0-ipv6:
      ifname: eth0
      address: 2002:42D0:8:2202::1
      netmask: 64
      gateway:
      dnsservers: 127.0.0.1 212.126.32.92 8.8.8.8 4.4.4.4
      post-up:
        - /sbin/ip -f inet6 route add 2002:4120:2:2Fff:ff:ff:ff:ff dev eth0
        - /sbin/ip -f inet6 route add default via 2002:4120:2:2Fff:ff:ff:ff:ff
      pre-down:
        - /sbin/ip -f inet6 route del default via 2002:4120:2:2Fff:ff:ff:ff:ff
        - /sbin/ip -f inet6 route del 2002:4120:2:2Fff:ff:ff:ff:ff dev eth0


with explicit order

.. code-block:: yaml

    makina-states.localsettings.network.ointerfaces
        - em1: {} # -> dhcp based interface
        - eth0-ipv6:
              ifname: eth0
              address: 2002:42D0:8:2202::1
              netmask: 64
              gateway:
              dnsservers: 127.0.0.1 212.126.32.92 8.8.8.8 4.4.4.4
              post-up:
                - /sbin/ip -f inet6 route add 2002:4120:2:2Fff:ff:ff:ff:ff dev eth0
                - /sbin/ip -f inet6 route add default via 2002:4120:2:2Fff:ff:ff:ff:ff
              pre-down:
                - /sbin/ip -f inet6 route del default via 2002:4120:2:2Fff:ff:ff:ff:ff
                - /sbin/ip -f inet6 route del 2002:4120:2:2Fff:ff:ff:ff:ff dev eth0
        - eth0:
              address: 8.1.5.4
              netmask: 255.255.255.0
              gateway: 8.1.5.1
              dnsservers: 8.8.8.8


