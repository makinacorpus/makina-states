{# nagvis macro helpers #}
{#
# Macros mains args:
#     name
#         the filename of map without extension
#     _global
#         dictionary which contains directives for 'define global {}'
#     objects
#         dictionary where each key contains a subdictionary. Each key concerns
#         a type of objects such as
#         'host', 'service', 'hostgroup', 'servicegroup', 'shape', ...
#         in each subdictionary, the subsubdictionaries contains directives 
#         for the 'define <type>{}'
#     keys_mapping
#         dictionary to do the associations between keys of dictionaries and directive
#         for example the keys in the "host" subdctionary are values for "host_name" directive
#         if the value is None, the dictionary become a list (it will be usefull because sometimes
#         no directive has a unique value)
#
#
#     {
#         'name': "test",
#         '_global': {
#             'object_id': 0,
#             'iconset': "std_medium",
#         },
#         'objects': {
#             'host': {
#                 'host1': {
#                     'x': 4,
#                     'y': 3,
#                 },
#             },
#             'service': {
#                 'SSH': {
#                     'host_name': "host1",
#                 },
#             },
#         },
#     },
#}
{%
    set keys_mapping_default = {
      'host': "host_name",
      'hostgroup': "hostgroup_name",
      'service': "service_description",
      'servicegroup': "servicegroup_name",
      'map': "map_name",
      'textbox': None,
      'shape': None,
      'line': None,
      'template': None,
      'container': None,
    }

%}
{% macro add_map(name, _global={}, objects={}, keys_mapping=keys_mapping_default) %}
{% set data = salt['mc_nagvis.add_map_settings'](name, _global, objects, keys_mapping, **kwargs) %}
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
#         dictionary in which each subdictionary defines a host
#
#     {
#         'name': "test",
#         'hosts': {
#             'ham-srv1': {
#                 'alias': "Hamburg Server 1",
#                 'lat': 53.556866,
#                 'lon': 9.994622,
#             },
#             'mun-srv1': {
#                 'alias': "Munich Server 1",
#                 'lat': 48.1448353,
#                 'lon': 11.5580067,
#             },
#         },
#     }
#}
{% macro add_geomap(name, hosts={}) %}
{% set data = salt['mc_nagvis.add_geomap_settings'](name, hosts, **kwargs) %}
{% set sdata = salt['mc_utils.json_dump'](data) %}

# add the csv file into geomap directory
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


