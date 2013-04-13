include:
  - makina-states.controllers.hooks

{%- set locs = salt['mc_locations.settings']() %}
{%- set settings = salt['mc_salt.settings']() %}
{%- set pathid = salt['mc_utils.hash'](settings.msr, typ='md5') %}
{%- set bootsalt= '{0}/_scripts/boot-salt.sh'.format(settings.msr) %}

{% for bin in ['ansible',
               'ansible-playbook',
               'salt-call',
               'boot-salt.sh'] %}
salt-{{bin}}-bootsalt-link-bin:
  file.symlink:
    - name: /usr/local/bin/{{bin}}
    - target: {{ settings.msr }}/_scripts/{{bin}}
    - require_in:
      - mc_proxy: dummy-pre-salt-service-restart
{% endfor %}
