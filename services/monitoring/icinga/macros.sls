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
{% macro add_configuration(rand, objects={}, directory, keys_mapping=keys_mapping_default, accumulated_values=accumulated_values_default) %}
{% set data = salt['mc_icinga.add_configuration_settings'](objects, directory, keys_mapping, accumulated_values, **kwargs) %}
{% set sdata = salt['mc_utils.json_dump'](data) %}

# loop over types
{% for type, objs in objects.items() %}

{% if None == data.keys_mapping[type] %}
    {% set key_map_is_directive = False %}
{% else %}
    {% set key_map_is_directive = True %}
{% endif %}


# loop over objects
{% for key_map, object in objs.items() %}


# we fill accumulators for accumulated attributes
{% for key, value in object.items() %}
{% if key in accumulated_values[type] %}

icinga-{{rand}}-configuration-{{type}}-{{key_map}}-attribute-{{key}}-accumulated:
  file.accumulated:
    - name: "{{type}}-{{key_map}}-attribute-{{key}}"
    - filename: {{data.directory}}/{{type}}/{{key_map}}.cfg
    - text: "{{value}}"
    - watch:
      - mc_proxy: icinga-pre-conf
    - watch_in:
      - mc_proxy: icinga-post-conf
      - file: icinga-{{rand}}-configuration-{{type}}-{{key_map}}-object-conf
{% endif %}
{% endfor %}


# we add the definition of object
icinga-{{rand}}-configuration-{{type}}-{{key_map}}-object-conf:
  file.managed:
    - name: {{data.directory}}/{{type}}/{{key_map}}.cfg
    - user: root
    - group: root
    - mode: 644
    - makedirs: True
    - watch:
      - mc_proxy: icinga-pre-conf
    - watch_in:
      - mc_proxy: icinga-post-conf
    - template: jinja
    - contents: |
               define {{type}} {
               {%- if key_map_is_directive %}
                {{keys_mapping[type]}}={{key_map}}
               {% endif -%}
               {%- for key, value in object.items() %}
               {%- if (not key_map_is_directive) or (key_map != key) -%}
               {%- if key in accumulated_values[type] -%}
                {{key}}=
                {% for values in accumulator['{{type}}-{{key_map}}-attribute-{{key}}'] %}{{ value }},{% endfor %}
               {% else %}
                {{key}}={{value}}
               {% endif -%}
               {%- endif -%}
               {% endfor -%}
               }


# endloop over objects
{% endfor %}

# endloop over types
{% endfor %}

{% endmacro %}

