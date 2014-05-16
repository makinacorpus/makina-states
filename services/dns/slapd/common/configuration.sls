{% set pkgssettings = salt['mc_pkgs.settings']() %}
{% set settings = salt['mc_slapd.settings']() %}
{% set yameld_data = salt['mc_utils.json_dump'](settings) %}
{% if salt['mc_controllers.mastersalt_mode']() %}
include:
  - makina-states.services.dns.slapd.hooks
  - makina-states.services.dns.slapd.services

slapd-dirs:
  file.directory:
    - names:
      {% for d in settings.extra_dirs %}
      - "{{d}}"
      {% endfor %}
    - makedirs: true
    - user: root
    - group: {{settings.group}}
    - mode: 775
    - watch_in:
      - mc_proxy: slapd-pre-conf
    - watch:
      - mc_proxy: slapd-post-install

named_directory:
  file.directory:
    - name: {{ settings.slapd_directory }}
    - user: {{settings.user}}
    - group: {{settings.group}}
    - mode: 775
    - makedirs: True
    - watch:
      - mc_proxy: slapd-post-install
    - watch_in:
      - mc_proxy: slapd-pre-conf


{% for tp in [
  '/etc/default/slapd',
] %}
slapd_config_{{tp}}:
  file.managed:
    - name: {{tp}}
    - makedirs: true
    - source: source://makina-states/files{{tp}}
    - template: jinja
    - user: {{settings.user}}
    - group: {{settings.group}}
    - mode: {{settings.mode}}
    - defaults:
      data: |
            {{yameld_data}}
    - watch:
      - mc_proxy: slapd-pre-conf
    - watch_in:
      - mc_proxy: slapd-post-conf
{% endfor %}


{% for tp in [] %}
slapd_config_{{tp}}:
  file.managed:
    - name: {{ settings['{0}_config'.format(tp)]}}
    - source: {{settings['{0}_config_template'.format(tp)]}}
    - template: jinja
    - makedirs: true
    - user: {{settings.user}}
    - group: {{settings.group}}
    - mode: {{settings.mode}}
    - defaults:
      data: |
            {{yameld_data}}
    - watch:
      - mc_proxy: slapd-pre-conf
    - watch_in:
      - mc_proxy: slapd-post-conf
{% endfor %}
{% endif %}
