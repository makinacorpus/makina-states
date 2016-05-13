{%- import "makina-states/_macros/h.jinja" as h with context %}
{%- set vmdata = salt['mc_cloud_vm.settings']() %}
{%- set settings = vmdata.vts.lxc %}
{%- set pm = salt['mc_services_managers.get_processes_manager'](settings) %}
{%- set service_function = salt['mc_services_managers.get_service_function'](pm) %}

include:
  - makina-states.services.firewall.ms_iptables.hooks
  - makina-states.services.virt.lxc.hooks
  - makina-states.services.virt.cgroups

{% macro reloadc() %}
    - watch:
      - mc_proxy: lxc-pre-restart
      - mc_proxy: lxc-services-others-pre
    - watch_in:
      - mc_proxy: lxc-services-others-post
{% endmacro %}
{{ h.service_restart_reload('apparmor',
                            service_function=service_function,
                            pref='makina-lxc',
                            restart_macro=reloadc,
                            reload_macro=reloadc) }}

{# sperate states used for ms_iptables, to avoid circular loops #}
{% macro reloada() %}
    - watch:
      - mc_proxy: ms_iptables-postrestart
      - mc_proxy: lxc-pre-restart
      - mc_proxy: lxc-net-services-enabling-pre
    - watch_in:
      - mc_proxy: lxc-net-services-enabling-post
{% endmacro %}
{% for i in ['lxc-net', 'lxc-net-makina'] %}
{{ h.service_restart_reload(i,
                            service_function=service_function,
                            pref='makina-lxc',
                            reload=False,
                            restart_macro=reloada,
                            reload_macro=reloada) }}
{% endfor %}

{% macro reloadb() %}
    - require:
      - mc_proxy: lxc-pre-restart
      - mc_proxy: lxc-services-enabling-pre
    - watch:
      - mc_proxy: lxc-post-pkg
    - watch_in:
      - mc_proxy: lxc-services-enabling-post
{% endmacro %}
{{ h.service_restart_reload('lxc',
                            service_function=service_function,
                            pref='makina-lxc',
                            reload=False,
                            restart_macro=reloadb,
                            reload_macro=reloadb) }}
