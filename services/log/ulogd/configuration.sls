{% set data = salt['mc_ulogd.settings']() %}
include:
  - makina-states.services.log.ulogd.hooks
{% if salt['mc_controllers.mastersalt_mode']() %}
  - makina-states.services.log.ulogd.services

makina-ulogd-configuration-check:
  cmd.run:
    - name: /bin/true && echo "changed=no"
    - stateful: true
    - watch:
      - mc_proxy: ulogd-post-conf-hook
    - watch_in:
      - mc_proxy: ulogd-pre-restart-hook

{% set sdata =salt['mc_utils.json_dump'](data) %}
{% for f in [
'/etc/ulogd.conf',
] %}
makina-ulogd-{{f}}:
  file.managed:
    - name: {{f}}
    - makedirs: true
    - source: salt://makina-states/files{{f}}
    - user: root
    - group: root
    - mode: 755
    - template: jinja
    - defaults:
      data: |
            {{sdata}}
    - watch:
      - mc_proxy: ulogd-pre-conf-hook
    - watch_in:
      - mc_proxy: ulogd-post-conf-hook
{% endfor %}

{%endif %}
