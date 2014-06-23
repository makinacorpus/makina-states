{# nagvis macro helpers #}
{#
# Macros mains args:
#     name
#         the filename of map without extension
#     _global
#         dictionary which contains directives for 'define global {}'
#     hosts
#         dictionary which each subdictionary contains directives for 'define host{}'
#         'object_id' directive is set with the key of subdictionary
#     services
#         dictionary which each subdictionary contains directives for 'define service{}'
#         'object_id' directive is set with the key of subdictionary
#     hostgroups
#         dictionary which each subdictionary contains directives for 'define hostgroup{}'
#         'object_id' directive is set with the key of subdictionary
#     servicegroups
#         dictionary which each subdictionary contains directives for 'define servicegroup{}'
#         'object_id' directive is set with the key of subdictionary
#
#
#     {
#         'name': "test",
#         '_global': {
#             'object_id': 0,
#             'iconset': "std_medium",
#         },
#         'hosts': {
#             'abc': {
#                 'host_name': "host1",
#                 'x': 4,
#                 'y': 3,
#             },
#         },
#         'services': {
#             'def': {
#                 'host_name': "host1",
#                 'service_description': "SSH",
#                 'x': 4,
#                 'y': 3,
#             },
#         },
#         'hostgroups': {
#         }
#         'servicesgroups': {
#         }
#     }
#}
{% macro add_map(name, _global={}, hosts={}, services={}, hostgroups={}, servicegroups={}) %}
{% set data = salt['mc_nagvis.add_map_settings'](name, _global, hosts, services, hostgroups, servicesgroups, **kwargs) %}
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


