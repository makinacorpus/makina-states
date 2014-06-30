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
      - mc_proxy: icinga-configuration-pre-clean-directories
    - watch_in:
      - mc_proxy: icinga-configuration-post-clean-directories

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


{% macro configuration_add_auto_host(name, attrs={}, ssh_user) %}
{% set data = salt['mc_icinga.add_auto_configuration_host_settings'](name, attrs, ssh_user, **kwargs) %}
{% set sdata = salt['mc_utils.json_dump'](data) %}
{% set ssh_command = 'ssh -q '+data.ssh_user+'@'+data.attrs['address']+' ' %}

# we add the host object
{{ configuration_add_object(type='host', name=data.name, attrs=data.attrs) }}

# we connect to ssh and get the mc_localsettings.registry, mc_services.registry and grains
{% set host_services_registry = salt['cmd.run'](ssh_command+'salt-call --out=json mc_services.registry') %}
{% set host_localsettings_registry = salt['cmd.run'](ssh_command+'salt-call --out=json mc_localsettings.registry') %}
{% set host_grains = salt['cmd.run'](ssh_command+'salt-call --out=json grains.items') %}
# and transform str to json
{% set host_services_registry = salt['mc_utils.json_load'](host_services_registry) %}
{% set host_localsettings_registry = salt['mc_utils.json_load'](host_localsettings_registry) %}
{% set host_grains = salt['mc_utils.json_load'](host_grains) %}

# if ssh is active we add a SSH service
{% if host_services_registry.local.actives['base.ssh'] %}
    {% set ssh_port = salt['cmd.run'](ssh_command+'"grep -E \'^([ \t]*)Port\' /etc/ssh/sshd_config" | awk \'{print $2}\'') %}
    # python doesn't like
    {#{% set default_ssh_port =  salt['cmd.run']('sed -ne \'s#^ssh\([^0-9]\+\)\([0-9]*\)/tcp\(.*\)#\2#p\' /etc/services') %}#}
    {% set default_ssh_port = salt['cmd.run']('grep ssh /etc/services | awk \'{print $2}\' | grep tcp | awk -F \'/\' \'{print $1}\'') %}

    {% set ssh_port= default_ssh_port if (''==ssh_port) else ssh_port %}
    {{ configuration_add_object(type='service',
                            name="SSH_"+data.name,
                            attrs= {
                             'service_description': "SSH port "+ssh_port,
                             'host_name': data.name,
                             'use': "generic-service",
                             'check_command': "check_ssh!"+ssh_port,
                            }
       ) }}

{% endif %}

# get mountpoints


# TODO: find ssh_port in grains or localsettings
#       find mountpoints from grains or localsettings

{% endmacro %}

