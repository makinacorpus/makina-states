{#-
# sysctl configuration for system optimization
#
#  https://publib.boulder.ibm.com/infocenter/clresctr/vxrx/index.jsp?topic=%2Fcom.ibm.cluster.pe.v1r3.pe200.doc%2Fam101_tysfbpjp.htm
#}
include:
  - makina-states.localsettings.sysctl.hooks

{{ salt['mc_macros.register']('localsettings', 'sysctl') }}
{% if salt['mc_controllers.allow_lowlevel_states']() %}
{% set kernel = salt['mc_kernel.settings']() %}
{% set isTravis = salt['mc_nodetypes.is_travis']() %}
{% if not (isTravis or salt['mc_nodetypes.is_container']()) %}
{# increase the length of the processor input queue #}
sysctl-net.core.somaxconn:
  sysctl.present:
    - name: net.core.somaxconn
    - value: {{kernel.net_core_somaxconn}}
    - require_in:
      - mc_proxy: sysctl-post-hook

sysctl-tcp_max_sync_backlog:
  sysctl.present:
    - name: net.ipv4.tcp_max_syn_backlog
    - value: {{kernel.tcp_max_syn_backlog}}
    - require_in:
      - mc_proxy: sysctl-post-hook

sysctl-net-backlog:
  sysctl.present:
    - name: net.core.netdev_max_backlog
    - value: {{kernel.netdev_max_backlog}}
    - require_in:
      - mc_proxy: sysctl-post-hook

sysctl-net-tcp_no_metrics_save:
  sysctl.present:
    - name: net.ipv4.tcp_no_metrics_save
    - value: {{kernel.no_metrics_save}}
    - require_in:
      - mc_proxy: sysctl-post-hook

sysctl-net-tcp_max_tw_buckets:
  sysctl.present:
    - name: net.ipv4.tcp_max_tw_buckets
    - value: {{kernel.tcp_max_tw_buckets}}
    - require_in:
      - mc_proxy: sysctl-post-hook

sysctl-net.ipv4.tcp_tw_recycle:
  sysctl.present:
    - name: net.ipv4.tcp_tw_recycle
    - value: {{kernel.tcp_tw_recycle}}
    - require_in:
      - mc_proxy: sysctl-post-hook

sysctl-net.ipv4.tcp_syn_retries:
  sysctl.present:
    - name: net.ipv4.tcp_syn_retries
    - value: {{kernel.tcp_syn_retries}}
    - require_in:
      - mc_proxy: sysctl-post-hook

sysctl-net.ipv4.tcp_fin_timeout:
  sysctl.present:
    - name: net.ipv4.tcp_fin_timeout
    - value: {{kernel.tcp_fin_timeout}}
    - require_in:
      - mc_proxy: sysctl-post-hook

sysctl-net.ipv4.tcp_tw_reuse:
  sysctl.present:
    - name: net.ipv4.tcp_tw_reuse
    - value: {{kernel.tcp_tw_reuse}}
    - require_in:
      - mc_proxy: sysctl-post-hook

{# Enable timestamps as defined in RFC1323: #}
sysctl-net.ipv4.tcp_timestamps:
  sysctl.present:
    - name: net.ipv4.tcp_timestamps
    - value: {{kernel.tcp_timestamps}}
    - require_in:
      - mc_proxy: sysctl-post-hook
sysctl-net.ipv4.vm.min_free_kbytes:
  sysctl.present:
    - name: vm.min_free_kbytes
    - value: {{kernel.vm_min_free_kbytes}}
    - require_in:
      - mc_proxy: sysctl-post-hook

sysctl-vm.swappiness:
  sysctl.present:
    - names:
      - vm.swappiness
    - value: {{kernel.vm_swappiness}}
    - require_in:
      - mc_proxy: sysctl-post-hook

sysctl-net-ip_local_port_range:
  sysctl.present:
    - name: net.ipv4.ip_local_port_range
    - value: {{kernel.ip_local_port_range}}
    - require_in:
      - mc_proxy: sysctl-post-hook

{# increase TCP max buffer size settable using setsockopt() #}
sysctl-net.core.rmem__wmem_max:
  sysctl.present:
    - names:
      - net.core.rmem_max
      - net.core.wmem_max
    - value: {{kernel.rwmemmax}}
    - require_in:
      - mc_proxy: sysctl-post-hook

{# increase Linux autotuning TCP buffer limit #}
sysctl-net.ipv4.tcp_rmem:
  sysctl.present:
    - names:
      - net.ipv4.tcp_rmem
    - value: {{kernel.tcp_rmem}}
    - require_in:
      - mc_proxy: sysctl-post-hook
sysctl-net.ipv4.tcp_wmem:
  sysctl.present:
    - names:
      - net.ipv4.tcp_wmem
    - value:  {{kernel.tcp_wmem}}
    - require_in:
      - mc_proxy: sysctl-post-hook

sysctl-net-congestionprotocol:
  sysctl.present:
    - name: net.ipv4.tcp_congestion_control
    - value: {{kernel.tcp_congestion_control}}
    - require_in:
      - mc_proxy: sysctl-post-hook

sysctl-net-various:
  sysctl.present:
    - names:
      {# Enable select acknowledgments #}
      - net.ipv4.tcp_sack
      - net.ipv4.tcp_fack
      {# to take advantage of net.ipv4.tcp_max_syn_backlog= tuning #}
      - net.ipv4.tcp_syncookies
      {# Turn on window scaling which can be an option to enlarge the transfer window: #}
      - net.ipv4.tcp_window_scaling
      - net.ipv4.tcp_moderate_rcvbuf
    - value: 1
    - require_in:
      - mc_proxy: sysctl-post-hook
{% for s, val in kernel.items() %}
{% if '.' in s %}
sysctl-{{s}}:
  sysctl.present:
    - name: {{s}}
    - value: {{val}}
    - require_in:
      - mc_proxy: sysctl-post-hook
{% endif %}
{% endfor %}
{% endif %}
{% endif %}
# vim: set nofoldenable:
