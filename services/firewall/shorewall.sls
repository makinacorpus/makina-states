# Shoreline Firewall (shorewall) configuration
#
# Configuration is based on pillar information
# As of all makina states, you can use something in
# (*-)makina-shorewall to configure shorewall*
# The states will be aggregated (inclusion then alphabetic order)
#
# Configure the pillar to enable shorewall service:
# Think that in yaml you can nest mappings as {}
#
#  toto:     is equilalent to toto: {a:1}
#    a: 1
#
# Enable shorewall service::
# in config (pillar, grain
#
#   makina.services.shorewall.enabled: True | False
#
# Defining shorewall interfaces:
#   interfaces:
#     shorewall-interface-name:
#       interface: phyname
#       options: shorewall options
#   EG:
#     thishost-makina-shorewall:
#       interfaces:
#         net:
#           interface: eth0
#           options: tcpflags,dhcp,nosmurfs,routefilter,logmartians,sourceroute=0
#
# Masquerade configuration:
#   masq:
#     interface-comment:
#       interface: ifname
#       source: (opt)
#       address: (opt)
#       proto: (opt)
#       ports: (opt)
#       ipsec: (opt)
#       mark: (opt)
#   EG:
#     thishost-makina-shorewall:
#       masq:
#         lxc:
#           interface: eth0
#           source: lxcbr0
#
# Params configuration:
#   params:
#     param: value
#   EG:
#     thishost-makina-shorewall:
#       params:
#         thishostguest: 10.0.3.2
#
# Zones configuration
#   zones:
#     fw:
#       type: zone type
#       options: (opt)
#       in: (opt)
#       out: (opt)
#       in_options: (opt)
#       out_options: (opt)
#   EG:
#     thishost-makina-shorewall:
#       zones:
#         fw:  {type: firewall}
#         net: {type: ipv4}
#         lxc: {type: ipv4}
#
# Policy configuration
#   rules (list of dict):
#     - source: shorewall zone
#       dest: shorewall zone
#       policy: policy
#       loglevel: loglevel (opt)
#       limit: limit:burst (opt)
#   EG:
#     thishost-makina-shorewall:
#       policy:
#         - {source: $FW, dest: net, policy: ACCEPT,}
#         - {source: rpn, dest: all, policy: DROP, loglevel: info}
#         - {source: all, dest: all, policy: REJECT, loglevel: info}
#
# Rules configuration
#   rules (list of dict):
#      - section: new (default) : established | related | all (opt)
#        action: action todo
#        source: source addr
#        dest: dest addr
#        proto: (opt)
#        dport: (opt)
#        sport: (opt)
#        odest: (opt)
#        rate: (opt)
#        user: (opt)
#        mark: (opt)
#        connlimit: (opt)
#        time: (opt)
#        headers: (opt)
#        switch: (opt)
#   EG:
#     thishost-makina-shorewall:
#       rules:
#         - {section: established, action: Invalid(DROP), source: net, dest: all}
#         - {action: Invalid(DROP), source: net, dest: all}
#         - {action: DNS(ACCEPT),   source: all, dest: all}
#         - {action: SSH(ACCEPT),   source: all, dest: all}
#         - {action: Ping(ACCEPT),  source: all, dest: all}
#         - {action: Ping(DROP),    source: net, dest: $FW}
#         - {comment: 'thishostguest lxc'}
#         - {action: DNAT, source: net, dest: 'lxc:${thishostguest}:80', proto: tcp, dport: 8082}
#         - {comment: 'dhcp in lxc'}
#         - {action: ACCEPT, source: lxc, dest: fw , proto: udp, dport: '67:68'}
#         - {action: ACCEPT, source: fw , dest: lxc, proto: udp, dport: '67:68'}
#         - {comment: 'salt'}
#         - {action: ACCEPT, source: all, dest: fw, proto: 'tcp,udp', dport: '4506,4505'}
#         - {comment: 'relay smtp from lxc and drop from net'}
#         - {action: Invalid(DROP), source: net, dest: all, proto: 'tcp,udp', dport: 25}
#         - {action: ACCEPT       , source: lxc, dest: fw , proto: 'tcp,udp', dport: 25}

{% import "makina-states/_macros/services.jinja" as services with context %}
{% set localsettings = services.localsettings %}
{% set nodetypes = services.nodetypes %}
{% set locs = localsettings.locations %}
{{ services.register('firewall.shorewall') }}
include:
  - {{ localsettings.statesPref }}localrc

{% set ishorewallen = 'firewall.shorewall' in services.services %}

shorewall-pkgs:
  pkg.installed:
    - pkgs:
      - shorewall6
      - shorewall

shorewall-test-cfg:
  file.exists:
    - name: {{ locs.conf_dir }}/shorewall/shorewall.conf

shorewall-restart:
  cmd.run:
    - name: {{ locs.conf_dir }}/rc.local.d/shorewall.sh fromsalt
    - stateful: True
    - require:
      - pkg: shorewall-pkgs
    - require:
      - file: shorewall-rc-local-d
      - pkg: shorewall-pkgs

shorewall-config:
  file.recurse:
    - name: {{ locs.conf_dir }}/shorewall
    - source : salt://makina-states/files/etc/shorewall
    - template: jinja
    - user: root
    - group: root
    - defaults:
      - shwData: {{ services.shwData | yaml }}
    - require_in:
      - file: toggle-shorewall
      - cmd: shorewall-restart

toggle-shorewall:
  file.replace:
    - name: {{ locs.conf_dir }}/default/shorewall
    - pattern: 'startup\s*=\s*(0|1|True|False)'
    - repl: 'startup={{ services.shw_enabled }}'
    - flags: ['MULTILINE', 'DOTALL']
    - require_in:
      - cmd: shorewall-restart
      - file: rc-local

shorewall-e:
  service.dead:
    - names:
      - shorewall
      - shorewall6
    - enable: False
    - require_in:
      - cmd: shorewall-restart

shorewall-d:
  service.disabled:
    - names:
      - shorewall
      - shorewall6
    - require_in:
      - cmd: shorewall-restart

# shorewall is not managed via init scripts as we really need
# everything to be up before firewall to cut the garden off.
shorewall-rc-local-d:
  file.managed:
    - name: {{ locs.conf_dir }}/rc.local.d/shorewall.sh
    - source : salt://makina-states/files/etc/rc.local.d/shorewall.sh
    - defaults:
      - shwData: {{ services.shwData | yaml }}
    - mode: 0755
    - template: jinja
    - user: root
    - group: root

# Disabled as we now use {{ locs.conf_dir }}/rc.local
# shorewall-upstart:
#   file.managed:
#     - name: {{ locs.upsteam }}/shorewall-upstart.conf
#     - source : salt://makina-states/files/etc/init/shorewall-upstart.conf
#     - template: jinja
#     - user: root
#     - group: root
#   service.running:
#     - require:
#       - file: shorewall-upstart
#       - service: shorewall-d
#       - service: shorewall-e
#     - enable: True
#     - watch:
#       - file: shorewall-test-cfg


