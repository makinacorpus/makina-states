{# icinga macro helpers #}
{#
#
# Macros mains args:
#     directory
#         the directory in which configuration must be written. The configuration files will be located
#         in subdirectories with a file for each defined object
#     objects
#         dictionary where the objects are defined
#     keys_mapping
#         dictionary to do the associations between keys of dictionaries and directive
#         for example the keys in the "host" subdictionary are values for "host_name" directive
#         if the value is None, key is an unique id which will not be transformed into a directive
#         but used for the filename
#     accumulated_values
#         dictionary to list the directives for which several values are allowed
#
#
#         the objects dictionary looks like:
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
      'host': ["use", "parents"],
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

# we clean the directory in order to remove old configuration
icinga-{{data.objects_hash}}-configuration-clean-directory:
  file.directory:
    - name: {{data.directory}}
    - user: root
    - group: root
    - dir_mode: 755
    - makedirs: True
    - clean: True
    - watch:
      - mc_proxy: icinga-pre-conf
    - watch_in:
      - mc_proxy: icinga-configuration-pre-accumulated-attributes-conf

# loop over types
{% for type, objs in objects.items() %}

# loop over objects
{% for key_map, object in objs.items() %}

# loop over attributes
# we fill accumulators for all attributes (it is bad but I don't find something better)
{% for key, value in object.items() %}

{% if key in accumulated_values[type] %}

# if the attribute can be accumulated, we split the value in ',' and loop. it is to remove duplicates values.
 {% for value_splitted in object[key].split(',') %}
icinga-{{data.objects_hash}}-configuration-{{type}}-{{key_map}}-attribute-{{key}}-{{value_splitted}}-accumulated:
  file.accumulated:
    - name: "{{type}}-{{key_map}}-attribute-{{key}}"
    - filename: {{data.directory}}/{{type}}/{{key_map}}.cfg
    - text: "{{value_splitted}}"
    - watch:
      - mc_proxy: icinga-configuration-pre-accumulated-attributes-conf
    - watch_in:
      - mc_proxy: icinga-configuration-post-accumulated-attributes-conf
      - file: icinga-{{data.objects_hash}}-configuration-{{type}}-{{key_map}}-object-conf
 {% endfor %}
{% else %}
# even if the attribute can't be accumulated, we use an accumulator in order to merge the keys obtained with differents calls
# for example in a call we have a=1 and in another we have b=2, we must merge "a=1\nb=2"
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

{% endif %}

# endloop over attributes
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

