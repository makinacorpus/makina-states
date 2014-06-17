{# uwsgi macro helpers #}
{#
# Macros mains args:
#
#     name
#      the name of configuration file
#     config_file
#      file to use for configuration
#     config_data
#      dictionary to fill the template
#     enabled
#      set to True in order to create a symbolic link in /etc/uwsgi/apps-enabled/
#}
{% macro app(name, config_file, config_data, enabled) %}
{% set data = salt['mc_uwsgi.settings']() %}
{% set sdata = salt['mc_utils.json_dump'](data) %}
{% set sconfigdata = salt['mc_utils.json_dump'](config_data) %}

uwsgi-{{name}}-conf:
  file.managed:
    - user: root
    - group: root
    - mode: 644
    - name: {{data.configuration_directory}}/apps-available/{{name}}.conf
    - source: {{config_file}}
    - template: jinja
    - makedirs: true
    - defaults:
        data: |
              {{sconfigdata}}
    - watch:
      - mc_proxy: uwsgi-pre-conf
    - watch_in:
      - mc_proxy: uwsgi-post-conf

{% if enabled %}
uwsgi-{{name}}-enable-conf:
  cmd.run:
    - name: ln -sf {{data.configuration_directory}}/apps-available/{{name}}.conf {{data.configuration_directory}}/apps-enabled/{{name}}.conf
    - watch:
      - mc_proxy: uwsgi-pre-conf
      - file: uwsgi-{{name}}-conf
    - watch_in:
      - mc_proxy: uwsgi-post-conf
{% endif %}

{% endmacro %}
