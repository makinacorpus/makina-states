{# icinga macro helpers #}

{#
#
# Macros mains args:
#     type
#         the type of added object
#     name
#         the name of the added object used for the filename
#     attrs
#         a dictionary in which each key corresponds to a directive
#
#}
{% macro configuration_add_object(type, name, attrs={}) %}
{% set data = salt['mc_icinga.add_configuration_object_settings'](type, name, attrs, **kwargs) %}
{% set sdata = salt['mc_utils.json_dump'](data) %}

# we clean the directory
icinga-configuration-{{data.type}}-{{data.name}}-clean-directory:
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

{#
#
# Macros mains args:
#     type
#         the type of edited object
#     name
#         the name of edited object
#     attr
#         the name of the edited directive
#     value
#         the value to append after the directive. The old value will not be removed
#
#}
{% macro configuration_edit_object(type, name, attr, value) %}
{% set data = salt['mc_icinga.edit_configuration_object_settings'](type, name, attr, value, **kwargs) %}
{% set sdata = salt['mc_utils.json_dump'](data) %}

# we split the value in ',' and loop. it is to remove duplicates values.
# for example, it is to avoid to produce "v1,v2,v1" if "v1,v2" are given in a call and "v1" in an other call
{% for value_splitted in data.value.split(',') %}
icinga-configuration-{{data.type}}-{{data.name}}-attribute-{{data.attr}}-{{value_splitted}}-conf:
  file.accumulated:
    - name: "{{data.attr}}"
    - filename: {{data.directory}}/{{data.type}}/{{data.name}}.cfg
    - text: "{{value_splitted}}"
    - watch:
      - mc_proxy: icinga-configuration-pre-accumulated-attributes-conf
    - watch_in:
      - mc_proxy: icinga-configuration-post-accumulated-attributes-conf
      - file: icinga-configuration-{{data.type}}-{{data.name}}-object-conf
{% endfor %}

{% endmacro %}
