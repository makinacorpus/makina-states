{# icinga macro helpers #}
{#
#
# Macros mains args:
#     file
#         the filename in which configuration must be written
#     objects
#         dictionary where the objects are defined
#     keys_mapping
#         dictionary to do the associations between keys of dictionaries and directive
#         for example the keys in the "host" subdctionary are values for "host_name" directive
#         if the value is None, key is an unique id which will not be transformed into a directive
#         but used for the filename
#
#         'objects': {
#             'host': {
#                 'hostname': {
#                     'key': 'value'
#                 },
#             },
#             'service': {
#                 'service_description': {
#                     'host_name': "host1",
#                 },
#             },
#             'servicedependency': {
#                 'abc': {},
#             },
#         },
#
#}
{%
    set keys_mapping_default = {
      'host': "host_name",
      'hostgroup': "hostgroup_name",
      'service': "service_description",
      'servicegroup': "servicegroup_name",
      'contact': "contact_name",
      'contactgroup': "contactgroup_name",
      'timeperiod': "timeperiod_name",
      'command': "command_name",
      'servicedependency': None,
      'serviceescalation': None,
      'hostdependency': None,
      'hostescalation': None,
      'hostextinfo': "host_name",
      'serviceextinfo': "host_name",
    }
%}{%
    set accumulated_values_default = {
      'host': ["parents", "attr"],
      'hostgroup': [],
      'service': [],
      'servicegroup': [],
      'contact': [],
      'contactgroup': [],
      'timeperiod': [],
      'command': [],
      'servicedependency': [],
      'serviceescalation': [],
      'hostdependency': [],
      'hostescalation': [],
      'hostextinfo': [],
      'serviceextinfo': [],
    }
%}
{% macro add_configuration(objects={}, directory, keys_mapping=keys_mapping_default, accumulated_values=accumulated_values_default) %}
{% set data = salt['mc_icinga.add_configuration_settings'](objects, directory, keys_mapping, accumulated_values, **kwargs) %}
{% set sdata = salt['mc_utils.json_dump'](data) %}

# loop over types
{% for type, objs in objects.items() %}

# loop over objects
{% for key_map, object in objs.items() %}

# we fill accumulators for all attributes (it is bad but I don't find something better)
{% for key, value in object.items() %}
icinga-{{data.objects_hash}}-configuration-{{type}}-{{key_map}}-attribute-{{key}}-accumulated:
  file.accumulated:
    - name: "{{type}}-{{key_map}}-attribute-{{key}}"
    - filename: {{data.directory}}/{{type}}/{{key_map}}.cfg
    - text: "{{object[key]}}"
    - watch:
      - mc_proxy: icinga-configuration-pre-accumulated-attributes-conf 
    - watch_in:
      - mc_proxy: icinga-configuration-post-accumulated-attributes-conf
      - file: icinga-{{data.objects_hash}}-configuration-{{type}}-{{key_map}}-object-conf
{% endfor %}


# we add the definition of object
icinga-{{data.objects_hash}}-configuration-{{type}}-{{key_map}}-object-conf:
  file.managed:
    - name: {{data.directory}}/{{type}}/{{key_map}}.cfg
    - source: salt://makina-states/files/etc/icinga/objects/template.cfg
    - user: root
    - group: root
    - mode: 644
    - makedirs: True
    - watch:
      - mc_proxy: icinga-configuration-pre-object-conf
    - watch_in:
      - mc_proxy: icinga-configuration-post-object-conf
    - template: jinja
    - defaults:
      data: |
            {{sdata}}
      type: |
            {{salt['mc_utils.json_dump'](type)}}
      key_map: |
               {{salt['mc_utils.json_dump'](key_map)}}
      object: |
              {{salt['mc_utils.json_dump'](object)}}


# endloop over objects
{% endfor %}

# endloop over types
{% endfor %}

{% endmacro %}

