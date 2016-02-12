include:
  - makina-states.services.base.ntp.hooks
  - makina-states.services.base.ntp.services
{%- set data = salt['mc_ntp.settings']() %}
{%- set sdata = salt['mc_utils.json_dump'](data) %}
{%- set locs = salt['mc_locations.settings']() %}
{% for cfg, cdata in data.configs.items() %}
{{cfg}}:
  file.managed:
    - watch_in:
      - mc_proxy: ntp-post-conf-hook
    - watch:
      - mc_proxy: ntp-pre-conf-hook
    - user: {{cdata.get('user', 'root')}}
    - group: {{cdata.get('group', 'root')}}
    - mode: {{cdata.get('mode', '0440')}}
    - source: {{cdata.get('source',
            'salt://makina-states/files'+cfg)}}
    - name: {{cdata.get('name', cfg)}}
    {% if cdata.get('template', 'jinja') %}
    - template: {{cdata.get('template', 'jinja')}}
    {% endif %}
{% endfor %}
