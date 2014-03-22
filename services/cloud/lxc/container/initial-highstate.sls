{% import "makina-states/_macros/localsettings.jinja" as localsettings with context %}
{% import "makina-states/_macros/nodetypes.jinja" as nodetypes with context %}
{% import "makina-states/_macros/salt.jinja" as saltmac with context %}
{% import "makina-states/_macros/services.jinja" as services with context %}
{% set cloudSettings= services.cloudSettings %}
{% set lxcSettings = services.lxcSettings %}

include:
  - makina-states.services.cloud.lxc.hooks

{% for target, containers in services.lxcSettings.containers.items() %}
{%  for k, data in containers.items() -%}
{%    set data = data.copy() %}
{%    do data.update({'state_name': '{0}-{1}'.format(target, k)})%}
{%    do data.update({'target': target})%}
{% set sname = data.get('state_name', data['name']) %}
{% set name = data['name'] %}
{% set clxcslsname = 'lxc.computenode.{0}-container-initial-hs'.format(sname.replace('.', '')) %}
{% if data['mode'] == 'mastersalt' %}
{% set salts = saltmac.msaltRoot %}
{% set msr = saltmac.msr %}
{% else %}
{% set salts = saltmac.saltRoot %}
{% set mmsr = saltmac.mmsr %}
{% endif %}
{% set clxcsls = '{1}/{0}.sls'.format(clxcslsname, salts) %}
c{{sname}}-lxc-initial-highstate:
  cmd.run:
    - name: ssh {{data.name}} "{{msr}}/_scripts/boot-salt.sh --initial-highstate"
    - user: root
    - watch:
      - mc_proxy: {{sname}}-lxc-deploy-pre-initial-highstate
    - watch_in:
      - mc_proxy: {{sname}}-lxc-post-setup-hook
{% endfor %}
{% endfor %}
