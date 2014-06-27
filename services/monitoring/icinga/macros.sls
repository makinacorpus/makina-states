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

{#
# we clean the directory in order to remove old configuration
icinga-configuration-clean-directory:
  file.directory:
    - name: 
    - user: root
    - group: root
    - dir_mode: 755
    - makedirs: True
    - clean: True
    - watch:
      - mc_proxy: icinga-pre-conf
    - watch_in:
      - mc_proxy: icinga-configuration-pre-accumulated-attributes-conf
#}


{% macro configuration_add_object(type, name, attrs={}) %}
{% set data = salt['mc_icinga.add_configuration_object_settings'](type, name, attrs, **kwargs) %}
{% set sdata = salt['mc_utils.json_dump'](data) %}

icinga-configuration-{{data.type}}-{{data.name}}-object-conf:
  file.managed:
    - name: {{data.directory}}/{{data.type}}/{{data.name}}.cfg
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

{% endmacro %}

{% macro configuration_edit_object(type, name, attr, value) %}
{% set data = salt['mc_icinga.edit_configuration_object_settings'](type, name, attr, value, **kwargs) %}
{% set sdata = salt['mc_utils.json_dump'](data) %}

icinga-configuration-{{data.type}}-{{data.name}}-attribute-{{data.attr}}-{{data.value}}-conf:
  file.accumulated:
    - name: "{{data.attr}}"
    - filename: {{data.directory}}/{{data.type}}/{{data.name}}.cfg
    - text: "{{data.value}}"
    - watch:
      - mc_proxy: icinga-configuration-pre-accumulated-attributes-conf
    - watch_in:
      - mc_proxy: icinga-configuration-post-accumulated-attributes-conf
      - file: icinga-configuration-{{data.type}}-{{data.name}}-object-conf

{% endmacro %}
