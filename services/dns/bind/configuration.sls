{% set pkgssettings = salt['mc_pkgs.settings']() %}
{% set settings = salt['mc_bind.settings']() %}
{% set yameld_data = salt['mc_utils.json_dump'](settings) %}
{% set zones = salt['mc_bind.cached_zone_headers']() %}

{% macro install_zone(zone) %}
{% set data = zones[zone] %}
dns-rzones-{{zone}}-{{data.fpath}}:
  file.managed:
    - name: {{ data.fpath}}
    {% if data.server_type == 'slave' %}
    - source: ''
    {% else %}
    {% if data.template %}
    - source: {{data.source}}
    - template: jinja
    - defaults:
      data: |
            {{salt['mc_utils.json_dump'](data)}}
    {% endif %}
    {% endif %}
    - user: {{settings.user}}
    - group: {{settings.group}}
    - mode: {{settings.mode}}
    - makedirs: true
    - watch:
      - mc_proxy: bind-pre-conf
    - watch_in:
      - mc_proxy: bind-post-conf
{% if data.server_type in ['master'] %}
bind-checkconf-{{zone}}-{{data.fpath}}:
  cmd.watch:
    - name: named-checkzone {{zone}} {{data.fpath}}
    {# do not trigger reload but report problems #}
    - unless: named-checkzone {{zone}} {{data.fpath}}
    - user: root
    - watch:
      - mc_proxy: bind-post-conf
    - watch_in:
      - mc_proxy: bind-check-conf
{% endif %}
{#
{% if data.dnssec %}
signed-{{file}}:
  cmd.run:
    - cwd: {{ settings.named_directory }}
    - name: zonesigner -zone {{ key }} {{ file }}
    - prereq:
      - file: zones-{{ file }}
      {% endif %}
{% endif %}
#}
{% endmacro %}

{% if salt['mc_controllers.mastersalt_mode']() %}
include:
  - makina-states.services.dns.bind.hooks
  - makina-states.services.dns.bind.services

bind-dirs:
  file.directory:
    - names:
      {% for d in settings.extra_dirs %}
      - "{{d}}"
      {% endfor %}
    - makedirs: true
    - user: root
    - group: bind
    - mode: 775
    - watch_in:
      - mc_proxy: bind-pre-conf
    - watch:
      - mc_proxy: bind-post-install

bind-/var/log/bind9:
  file.directory:
    - name: {{settings.log_dir}}
    - user: root
    - group: bind
    - mode: 775
    - watch_in:
      - mc_proxy: bind-pre-conf
    - watch:
      - mc_proxy: bind-post-install

named_directory:
  file.directory:
    - name: {{ settings.named_directory }}
    - user: {{settings.user}}
    - group: {{settings.group}}
    - mode: 775
    - makedirs: True
    - watch:
      - mc_proxy: bind-post-install
    - watch_in:
      - mc_proxy: bind-pre-conf

{% for tp in ['bind',
              'local',
              'key',
              'logging',
              'default_zones',
              'options',
              'acl',
              'servers',
              'views'] %}
bind_config_{{tp}}:
  file.managed:
    - name: {{ settings['{0}_config'.format(tp)]}}
    - source: {{settings['{0}_config_template'.format(tp)]}}
    - template: jinja
    - user: {{settings.user}}
    - group: {{settings.group}}
    - mode: {{settings.mode}}
    - defaults:
      data: |
            {{yameld_data}}
    - watch:
      - mc_proxy: bind-pre-conf
    - watch_in:
      - mc_proxy: bind-post-conf
{% endfor %}

rndc-key:
  cmd.run:
    - name: rndc-confgen -r /dev/urandom -a -c {{settings.rndc_key}}
    - unless: test -e {{settings.rndc_key}}
    - user: root
    - watch:
      - mc_proxy: bind-post-install
    - watch_in:
      - mc_proxy: bind-pre-conf
  file.managed:
    - name: {{settings.rndc_key}}
    - mode: 660
    - user: {{settings.user}}
    - group: {{settings.group}}
    - watch:
      - cmd: rndc-key
      - mc_proxy: bind-post-install
    - watch_in:
      - mc_proxy: bind-pre-conf

bind_config_rndc:
  file.managed:
    - name: {{settings.rndc_conf}}
    - source: {{settings.rndc_config_template}}
    - template: jinja
    - user: {{settings.user}}
    - group: {{settings.group}}
    - mode: {{settings.mode}}
    - defaults:
      data: |
            {{yameld_data}}
    - watch:
      - mc_proxy: bind-pre-conf
    - watch_in:
      - mc_proxy: bind-post-conf

{% for zone in settings.zones %}
{{ install_zone(zone) }}
{% endfor %}
{% endif %}
