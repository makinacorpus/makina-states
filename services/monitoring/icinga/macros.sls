{# icinga macro helpers #}
{#
# Macros mains args:
#     file
#         the filename in which configuration must be written
#     objects
#         dictionary where the objects are defined
#     keys_mapping
#         dictionary to do the associations between keys of dictionaries and directive
#         for example the keys in the "host" subdctionary are values for "host_name" directive
#         if the value is None, the dictionary become a list (it will be usefull because sometimes
#         no directive has a unique value)
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
icinga-configuration-{{data.file.basename_without_ext}}-conf:
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

icinga-configuration-add-accumulator

{% endmacro %}

{#
The goal of this macro is to complete files like commands.cfg, host.cfg,...
If the macro is called more than one time, we don't use define the services and hosts several times
We use an accumulator to do this
#}
{% set base_dir = "/etc/icinga/objects.cfg/" %}
{%
    set files_mapping_default = {
      'host': base_dir+"hosts.cfg",
      'hostgroup': base_dir+"hostgroups.cfg",
      'service': base_dir+"services.cfg",
      'servicegroup': base_dir+"servicegroups.cfg",
      'contact': base_dir+"contacts.cfg",
      'contactgroup': base_dir+"contactgroups.cfg",
      'timeperiod': base_dir+"timeperiods.cfg",
      'command': base_dir+"commands.cfg",
      'servicedependency': base_dir+"servicedependencies.cfg",
      'serviceescalation': base_dir+"serviceescalations.cfg",
      'hostdependency': base_dir+"hostdependencies.cfg",
      'hostescalation': base_dir+"hostescalations.cfg",
      'hostextinfo': base_dir+"hostextinfos.cfg",
      'serviceextinfo': base_dir+"serviceextinfos.cfg",
    }
%}

{% macro add_accumulated_configuration(objects={}, keys_mapping=keys_mapping_default, files_mapping=files_mapping_default) %}
{% set data = salt['mc_icinga.add_configuration_accumulated_settings'](objects, keys_mapping, files_mapping, **kwargs) %}
{% set sdata = salt['mc_utils.json_dump'](data) %}

{% for type, objs in objects %}

{% for key_map, objs in objs %}
icinga-accumulated-{{type}}-{{key_map}}-conf:
  file.accumulated:
    - name: icinga-accumulated-{{type}}-{{key_map}}-conf
    - filename: {{files_mapping[type]}}
    - text

{% endfor %}

{% endfor %}


{% endmacro %}

