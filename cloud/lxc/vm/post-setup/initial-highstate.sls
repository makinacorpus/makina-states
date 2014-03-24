{% set lxcSettings = salt['mc_cloud_lxc.settings']() %}
{% set cloudSettings = salt['mc_cloud.settings']() %}
include:
  - makina-states.services.cloud.lxc.hooks

{% for target, vms in lxcSettings.vms.items() %}
{%  for k, data in vms.items() -%}
{%    set data = data.copy() %}
{%    do data.update({'state_name': '{0}-{1}'.format(target, k)})%}
{%    do data.update({'target': target})%}
{% set sname = data.get('state_name', data['name']) %}
{% set name = data['name'] %}
{% set clxcslsname = 'lxc.computenode.{0}-vm-initial-hs'.format(sname.replace('.', '')) %}
{% set salts = cloudSettings.root %}
{% set msr = '{0}/makina-states'.format(salts) %}
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
