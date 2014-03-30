{#-
# sysctl configuration for system optimization
#
#  https://publib.boulder.ibm.com/infocenter/clresctr/vxrx/index.jsp?topic=%2Fcom.ibm.cluster.pe.v1r3.pe200.doc%2Fam101_tysfbpjp.htm
#}
include:
  - makina-states.localsettings.system.hooks

{% set localsettings = salt['mc_localsettings.settings']() %}
{{ salt['mc_macros.register']('localsettings', 'sysctl') }}
{% set locs = salt['mc_localsettings.settings']()['locations'] %}
{% set isLxc = nodetypes_registry.is.lxccontainer %}
{% set isTravis = nodetypes_registry.is.travis %}
{% if not (isTravis or isLxc) %}
{# increase TCP max buffer size settable using setsockopt() #}
sysctl-net.core.rmem__wmem_max:
  sysctl.present:
    - names:
      - net.core.rmem_max
      - net.core.wmem_max
    - value: {{localsettings.kernel.rwmemmax}}
    - require_in:
      - mc_proxy: sysctl-post-hook

{# increase Linux autotuning TCP buffer limit #}
sysctl-net.ipv4.tcp_rmem:
  syscl.present:
    - names:
      - net.ipv4.tcp_rmem
    - value: {{localsettings.kernel.tcp_rmem}}
    - require_in:
      - mc_proxy: sysctl-post-hook
sysctl-net.ipv4.tcp_wmem:
  syscl.present:
    - names:
      - net.ipv4.tcp_wmem
    - value:  {{localsettings.kernel.tcp_wmem}}
    - require_in:
      - mc_proxy: sysctl-post-hook

sysctl-net-ip_local_port_range:
  syscl.present:
    - name: net.ipv4.tcp_congestion_control
    - value: {{localsettings.kernel.ip_local_port_range}}
    - require_in:
      - mc_proxy: sysctl-post-hook

sysctl-net-congestionprotocol:
  syscl.present:
    - name: net.ipv4.tcp_congestion_control
    - value: {{localsettings.kernel.tcp_congestion_control}}
    - require_in:
      - mc_proxy: sysctl-post-hook

{# increase the length of the processor input queue #}
sysctl-tcp_max_sync_backlog:
  syscl.present:
    - name: net.ipv4.tcp_max_syn_backlog
    - value: {{localsettings.kernel.tcp_max_syn_backlog}}
    - require_in:
      - mc_proxy: sysctl-post-hook

sysctl-net-backlog:
  syscl.present:
    - name: net.core.netdev_max_backlog
    - value: {{localsettings.kernel.netdev_max_backlog}}
    - require_in:
      - mc_proxy: sysctl-post-hook

sysctl-net-tcp_no_metrics_save:
  syscl.present:
    - name: net.ipv4.no_metrics_save
    - value: {{localsettings.kernel.no_metrics_save}}
    - require_in:
      - mc_proxy: sysctl-post-hook
sysctl-net-tcp_max_tw_buckets:
  syscl.present:
    - name: net.ipv4.tcp_max_tw_buckets
    - value: {{localsettings.kernel.tcp_max_tw_buckets}}
    - require_in:
      - mc_proxy: sysctl-post-hook

sysctl-net.core.somaxconn:
  syscl.present:
    - name: net.core.somaxconn
    - value: {{localsettings.kernel.net_core_somaxconn}}
    - require_in:
      - mc_proxy: sysctl-post-hook

sysctl-net.ipv4.tcp_tw_recycle:
  syscl.present:
    - name: net.ipv4.tcp_tw_recycle
    - value: {{localsettings.kernel.tcp_tw_recycle}}
    - require_in:
      - mc_proxy: sysctl-post-hook

sysctl-net.ipv4.tcp_tw_reuse:
  syscl.present:
    - name: net.ipv4.tcp_tw_reuse
    - value: {{localsettings.kernel.tcp_tw_reuse}}
    - require_in:
      - mc_proxy: sysctl-post-hook

sysctl-net.ipv4.tcp_timestamps:
  syscl.present:
    - name: net.ipv4.tcp_timestamps
    - value: {{localsettings.kernel.tcp_timestamps}}
    - require_in:
      - mc_proxy: sysctl-post-hook

sysctl-net-various:
  syscl.present:
    - names:
      {# Enable timestamps as defined in RFC1323: #}
      - net.ipv4.tcp_timestamps
      {# Enable select acknowledgments #}
      - net.ipv4.tcp_sack
      {# Turn on window scaling which can be an option to enlarge the transfer window: #}
      - net.ipv4.tcp_window_scaling
    - value: 1
    - require_in:
      - mc_proxy: sysctl-post-hook
{% endif %}
# vim: set nofoldENABLE:
