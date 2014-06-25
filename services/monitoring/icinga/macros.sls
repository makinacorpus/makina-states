{# icinga macro helpers #}
{#
# A more simple script can be found in commit 9a65b2ce2cae9bbf2bd2cff22a558b890ea7f231
#
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
    set files_mapping_default = {
      'host': "hosts.cfg",
      'hostgroup': "hostgroups.cfg",
      'service': "services.cfg",
      'servicegroup': "servicegroups.cfg",
      'contact': "contacts.cfg",
      'contactgroup': "contactgroups.cfg",
      'timeperiod': "timeperiods.cfg",
      'command': "commands.cfg",
      'servicedependency': "servicedependency.cfg",
      'serviceescalation': "serviceescalation.cfg",
      'hostdependency': "hostdependency.cfg",
      'hostescalation': "hostescalation.cfg",
      'hostextinfo': "hostextinfo.cfg",
      'serviceextinfo': "serviceextinfo.cfg",
    }
%}{%
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
      'host': ['parents'],
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
{% macro add_configuration(rand, objects={}, directory, files_mapping=files_mapping_default, keys_mapping=keys_mapping_default) %}
{% set data = salt['mc_icinga.add_configuration_settings'](objects, directory, files_mapping, keys_mapping, **kwargs) %}
{% set sdata = salt['mc_utils.json_dump'](data) %}

# we use a blockreplace in order to avoid to have each objects more than one time in the file
# even if the macro is called several times

# loop over types
{% for type, objs in objects.items() %}

# we create the file if not exists
icinga-configuration-{{type}}-{{rand}}-create-file:
  file.managed:
    - name: {{data.files_mapping[type]}}
    - user: root
    - group: root
    - mode: 644
    - makedirs: True
    - watch:
      - mc_proxy: icinga-pre-conf
    - watch_in:
      - mc_proxy: icinga-post-conf

# loop over objects
{% if None == data.keys_mapping[type] %}
# the objects don't have unique value to differentiate them
    {% set unique = False %}
{% else %}
# the objects can be differencied. We can have only one object per unique value
    {% set unique = True %}
{% endif %}

{% for key_map, object in objs %}

# we add the definition of object
icinga-configuration-{{type}}-{{key_map}}-{{rand}}-conf:
  file.blockreplace:
    - name: {{data.files_mapping[type]}}
    - marker_start: "# BEGIN {{type}}-{{key_map}}"
    - marker_end: "# END {{type}}-{{key_map}}"
    - append_if_not_found: True
    - watch:
      - mc_proxy: icinga-pre-conf
      - file: icinga-configuration-{{type}}-{{rand}}-create-file
    - watch_in:
      - mc_proxy: icinga-post-conf
    - content: |
               define {{type}} {
               {%- for key, value in object.items() %}
                {{key}}={{value}}
               {% endfor -%}
               }


{% endfor %}

{% endfor %}

{% endmacro %}

