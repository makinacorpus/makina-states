{# nagvis macro helpers #}
{#
# Macros mains args:
#     name
#         the filename of map without extension
#     _global
#         dictionary which contains directives for 'define global {}'
#     objects
#         dictionary which each subdictionary contains directives for 'define object{}'
#         'object_id' directive is set with the key of subdictionary
#         'type' contains 'host', 'service', 'hostgroup', 'servicegroup', 'shape', ...
#
#     {
#         'name': "test",
#         '_global': {
#             'object_id': 0,
#             'iconset': "std_medium",
#         },
#         'objects': {
#             'abc': {
#                 'type': "host",
#                 'host_name': "host1",
#                 'x': 4,
#                 'y': 3,
#             },
#             'def': {
#                 'type': "service",
#                 'host_name': "host1",
#                 'service_description': "SSH",
#                 'x': 4,
#                 'y': 3,
#             },
#         },
#     }
#}
{% macro add_map(name, _global={}, objects={}) %}
{% set data = salt['mc_nagvis.add_map_settings'](name, _global, objects, **kwargs) %}
{% set sdata = salt['mc_utils.json_dump'](data) %}

nagvis-map-{{data.name}}-conf:
  file.managed:
    - user: root
    - group: root
    - mode: 644
    - name: {{data.configuration_directory}}/maps/{{data.name}}.cfg
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


{#
# Macros mains args:
#     name
#         the filename of geomap without extension
#     hosts
#         dictionary which each subdictionary defines a host
#
#     {
#         'name': "test",
#         'hosts': {
#             'ham-srv1': {
#                 'description': "Hamburg Server 1",
#                 'lat': 53.556866,
#                 'lon': 9.994622,
#             },
#             'mun-srv1': {
#                 'description': "Munich Server 1",
#                 'lat': 48.1448353,
#                 'lon': 11.5580067,
#             },
#         },
#     }
#}
{% macro add_geomap(name, hosts={}) %}
{% set data = salt['mc_nagvis.add_geomap_settings'](name, hosts, **kwargs) %}
{% set sdata = salt['mc_utils.json_dump'](data) %}

nagvis-geomap-{{data.name}}-conf:
  file.managed:
    - user: root
    - group: root
    - mode: 644
    - name: {{data.configuration_directory}}/geomap/{{data.name}}.csv
    - source: salt://makina-states/files/etc/nagvis/geomap/template.csv
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


