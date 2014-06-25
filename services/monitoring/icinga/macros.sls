{# icinga macro helpers #}
{#
# Macros mains args:
#     file
#         the filename in which configuration must be written
#     objects
#         dictionary where the objects are defined
#     keys_mapping
#         dictionary to do the association between key of dictionary and directive
#         for example the keys in the "host" subdctionarys are values for "host_name" directive
#         if the value is None, the type dictionary become a list (it will be usefull because sometimes
#         no directive has a unique value
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
#                     'service_description': "SSH",
#                 },
#             },
#             'servicedependency': [
#                 {},
#             ],
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
      'hostextinfo': 'host_name',
      'serviceextinfo': 'host_name',
    }

%}
{% macro add_configuration(file, objects={}, keys_mapping=keys_mapping_default) %}
{% set data = salt['mc_icinga.add_configuration_settings'](file, objects, keys_mapping, **kwargs) %}
{% set sdata = salt['mc_utils.json_dump'](data) %}
icinga-objects-{{data.file.basename_without_ext}}-conf:
  file.managed:
    - user: root
    - group: root
    - mode: 644
    - name: {{data.file.abspath}}
    - source: salt://makina-states/files/etc/icinga/objects/template.cfg
    - template: jinja
    - makedirs: true
    - defaults:
        data: |
              {{sdata}}
    - watch:
      - mc_proxy: icinga-pre-conf
    - watch_in:
      - mc_proxy: icinga-post-conf


{% endmacro %}


