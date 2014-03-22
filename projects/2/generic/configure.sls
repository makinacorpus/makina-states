{% import "makina-states/nodetypes/vagrantvm.sls" as vagrantvm with context %}
{% import "makina-states/_macros/salt.jinja" as saltmac with context %}
{% import "makina-states/_macros/services.jinja" as services with context %}
# export macro to callees
{% set services = services %}
{% set nodetypes = services.nodetypes %}
{% set localsettings = services.localsettings %}
{% set locs = salt['mc_localsettings.settings']()['locations'] %}
{% set saltmac = saltmac %}
{% set cfg = opts['ms_project'] %}
 {#-
# Register all the app domain's in /etc/hosts
# If we are in devmode (vagrant), also add them to the hosts to the parent box
#}
{% macro configure_domains(cfg) %}
{{cfg.name}}-append-etc-hosts-management:
  file.blockreplace:
    - name: {{ locs.conf_dir }}/hosts
    - marker_start: "#-- start project:{{cfg.name}} managed zoneend -- PLEASE, DO NOT EDIT"
    - marker_end: "#-- end project:{{cfg.name}} managed zoneend --"
    - content: ''
    - append_if_not_found: True
    - backup: '.bak'
    - show_changes: True

{{cfg.name}}-parent-etc-hosts-absent:
  file.absent:
    - name: {{vagrantvm.hostsf}}.{{cfg.name}}
    - require_in:
      - file: {{cfg.name}}-parent-etc-hosts-exists

{#-
# delete old stalled from import /etc/devhosts
# handle the double zone cases
#}
{{cfg.name}}-parent-etc-hosts-exists:
  file.touch:
    - name: {{vagrantvm.hostsf}}.{{cfg.name}}

{{cfg.name}}-append-parent-etc-hosts-management:
  file.blockreplace:
    - name: {{vagrantvm.hostsf}}.{{cfg.name}}
    - marker_start: '#-- start devhost {{vagrantvm.vmNum }} project:{{cfg.name}}:: DO NOT EDIT --'
    - marker_end: '#-- end devhost {{vagrantvm.vmNum }} project:{{cfg.name}}:: DO NOT EDIT --'
    - content: '# Vagrant vm: {{ vagrantvm.vm_fqdn }} added this entry via local mount:'
    - prepend_if_not_found: True
    - backup: '.bak'
    - show_changes: True
    - require:
      - file: {{cfg.name}}-parent-etc-hosts-exists

{%  if cfg.full and not cfg.no_domain %}
{{cfg.name}}-append-hosts-accumulator:
  file.accumulated:
    - name: hosts-append-accumulator-{{ cfg.name }}-entries
    - require_in:
      - file: {{cfg.name}}-append-etc-hosts-management
    - filename: {{ locs.conf_dir }}/hosts
    - text: |
            {% for domain in cfg.domains %}
            {{cfg.domains[domain]}} {{domain}}
            {% endfor %}

{# if we are on a vagrant box, also register our hosts
#  to be accesible from the host #}
{%-  if nodetypes.registry.is.vagrantvm %}
{%-    if vagrantvm.vmNum %}
makina-parent-append-etc-hosts-accumulated-project-{{cfg.name}}:
  file.accumulated:
    - filename: {{vagrantvm.hostsf}}.{{cfg.name}}
    - name: parent-hosts-append-accumulator-{{ vagrantvm.vm_name }}-{{cfg.name}}-entries
    - text: |
            {% for domain in cfg.domains %}
            {{ vagrantvm.ip2 }} {{domain}}
            {{ vagrantvm.ip1 }} {{domain}}
            {% endfor %}
    - require_in:
      - file: {{cfg.name}}-append-parent-etc-hosts-management
{%    endif %}
{%   endif %}
{%  endif %}
{% endmacro %} {# configure_domains #}
{% macro do() %}
{{configure_domains(cfg)}}
{% endmacro %}
{{do()}}
