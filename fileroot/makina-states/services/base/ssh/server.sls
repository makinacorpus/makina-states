{% import "makina-states/_macros/h.jinja" as h with context %}
{% import "makina-states/services/monitoring/circus/macros.jinja" as circus with context %}
{%- set locs = salt['mc_locations.settings']() %}
{% set openssh = salt['mc_ssh.settings']() %}
include:
  - makina-states.services.base.ssh.hooks
  - makina-states.services.base.ssh.services
opensshd-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - {{ openssh.pkg_server }}
    - watch_in:
      - mc_proxy: ssh-service-prerestart
sshgroup:
  group.present:
    - name: {{salt['mc_ssh.settings']().server.group}}
    - watch_in:
      - mc_proxy: ssh-service-prerestart

{% macro rmacro() %}
    - watch_in:
      - mc_proxy: ssh-service-prerestart
{% endmacro %}
{{ h.deliver_config_files(
     openssh.get('extra_confs', {}) , after_macro=rmacro, prefix='ssh-')}}
