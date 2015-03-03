{# uwsgi macro helpers #}
{#
# Macros mains args:
#
#     config_name
#      the name of configuration file
#     config_file
#      file to use for configuration
#     enabled
#      set to True in order to create a symbolic link in /etc/uwsgi/apps-enabled/
#}
{% macro config(config_name, config_file, enabled=True) %}
{% set data = salt['mc_uwsgi.config_settings'](config_name, config_file, enabled, **kwargs) %}
{% set sdata = salt['mc_utils.json_dump'](data) %}
uwsgi-{{config_name}}-conf:
  file.managed:
    - user: root
    - group: root
    - mode: 644
    - name: {{data.configuration_directory}}/apps-available/{{data.config_name}}
    - source: {{config_file}}
    - template: jinja
    - makedirs: true
    - defaults:
        data: |
              {{sdata}}
    - watch:
      - mc_proxy: uwsgi-pre-conf
    - watch_in:
      - mc_proxy: uwsgi-post-conf

{% if data.enabled %}
uwsgi-{{data.config_name}}-enable-conf:
  file.symlink:
    - name: {{data.configuration_directory}}/apps-enabled/{{data.config_name}}
    - target: {{data.configuration_directory}}/apps-available/{{data.config_name}}
    - watch:
      - mc_proxy: uwsgi-pre-conf
      - file: uwsgi-{{data.config_name}}-conf
    - watch_in:
      - mc_proxy: uwsgi-post-conf
{% endif %}
{% endmacro %}
