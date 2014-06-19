{% if grains['os_family'] in ['Debian'] %}
include:
  - makina-states.localsettings.pkgs.hooks
{% if salt['mc_controllers.mastersalt_mode']() %}
{%- set data = salt['mc_autoupgrade.settings']() %}
{% for f in [
  '/etc/apt/apt.conf.d/50unattended-upgrades',
  '/etc/apt/apt.conf.d/10periodic',
  ] %}
autoupgrade-conf-{{f}}:
  file.managed:
    - name: {{f}}
    - makedirs: True
    - source: salt://makina-states/files{{f}}
    - template: jinja
    - defaults:
      data: |
            {{salt['mc_utils.json_dump'](data)}}
    - user: root
    - group: root
    - mode: 644
    - watch_in:
      - mc_proxy: after-au-pkg-conf-proxy
    - watch:
      - mc_proxy: before-au-pkg-conf-proxy

{% endfor %}

{%endif %}
{%endif %}
