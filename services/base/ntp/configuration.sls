include:
  - makina-states.services.base.ntp.hooks
  - makina-states.services.base.ntp.services
{%- set data = salt['mc_ntp.settings']() %}
{%- set sdata = salt['mc_utils.json_dump'](data) %}
{%- set locs = salt['mc_locations.settings']() %}
{% if salt['mc_controllers.mastersalt_mode']() %}
{{ locs.conf_dir }}/ntp.conf:
  file.managed:
    - watch_in:
      - mc_proxy: ntp-post-conf-hook
    - watch:
      - mc_proxy: ntp-pre-conf-hook
    - user: root
    - group: root
    - mode: '0440'
    - template: jinja
    - source: salt://makina-states/files/etc/ntp.conf
    - var_lib: {{ locs.var_lib_dir }}
    - defaults:
      data: |
            {{sdata}}

{{ locs.conf_dir }}/default/ntpdate:
  file.managed:
    - watch_in:
      - mc_proxy: ntp-post-conf-hook
    - watch:
      - mc_proxy: ntp-pre-conf-hook
    - user: root
    - group: root
    - mode: '0440'
    - defaults:
      data: |
            {{sdata}}
    - template: jinja
    - source: salt://makina-states/files/etc/default/ntpdate
{% endif %}
