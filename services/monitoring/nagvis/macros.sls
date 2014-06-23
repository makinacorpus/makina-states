{# nagvis macro helpers #}
{#
# Macros mains args:
#
#     map_name
#      the name of the map
#     you must use **kwargs for parameters.
#     the dictionary looks like
#     {
#         'map_name': "test",
#         'global': {
#             'object_id': 0,
#             'iconset': "std_medium",
#         },
#         'hosts': {
#             'object_id': "abc",
#             'host_name': "foo",
#             'x': 4,
#             'y': 3,
#         },
#     }
#}
{% macro add_map(map_name) %}
{% set data = salt['mc_nagvis.add_map_settings'](map_name, **kwargs) %}
{% set sdata = salt['mc_utils.json_dump'](data) %}

nagvis-map-{{data.map_name}}-conf:
  file.managed:
    - user: root
    - group: root
    - mode: 644
    - name: {{data.configuration_directory}}/maps/{{data.map_name}}.cfg
    - source: salt://makina-states/files/etc/nagvis/maps/template.cfg
    - template: jinja
    - makedirs: true
    - defaults:
        data: |
              {{sdata}}
    - watch:
      - mc_proxy: nagvis-pre-conf
    - watch_in:
      - mc_proxy: nagvis-post-conf

{% endmacro %}


