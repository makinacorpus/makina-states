{# icinga macro helpers #}

{#
#
# Macros mains args:
#     type
#         the type of added object
#     file
#         the filename where the object will be added
#     attrs
#         a dictionary in which each key corresponds to a directive
#
#}

{% macro configuration_add_object(type, file, attrs={}) %}
{% set data = salt['mc_icinga.add_configuration_object_settings'](type, file, attrs, **kwargs) %}
{% set sdata = salt['mc_utils.json_dump'](data) %}

# we clean the directory
icinga-configuration-{{data.state_name_salt}}-clean-directory:
  file.directory:
    - name: {{data.objects_directory}}
    - user: root
    - group: root
    - dir_mode: 755
    - makedirs: True
    - clean: True
    - watch:
      - mc_proxy: icinga-configuration-pre-clean-directories
    - watch_in:
      - mc_proxy: icinga-configuration-post-clean-directories

# we add the object
icinga-configuration-{{data.state_name_salt}}-object-conf:
  file.managed:
    - name: {{data.objects_directory}}/{{data.file}}
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
#     file
#         the filename where is located the edited object
#     attr
#         the name of the edited directive
#     value
#         the value to append after the directive. The old value will not be removed
#
#}
{% macro configuration_edit_object(type, file, attr, value) %}
{% set data = salt['mc_icinga.edit_configuration_object_settings'](type, file, attr, value, **kwargs) %}
{% set sdata = salt['mc_utils.json_dump'](data) %}

# we split the value in ',' and loop. it is to remove duplicates values.
# for example, it is to avoid to produce "v1,v2,v1" if "v1,v2" are given in a call and "v1" in an other call
{% for value_splitted in data.value.split(',') %}
icinga-configuration-{{data.state_name_salt}}-attribute-{{data.attr}}-{{value_splitted}}-conf:
  file.accumulated:
    - name: "{{data.attr}}"
    - filename: {{data.objects_directory}}/{{data.file}}
    - text: "{{value_splitted}}"
    - watch:
      - mc_proxy: icinga-configuration-pre-accumulated-attributes-conf
    - watch_in:
      - mc_proxy: icinga-configuration-post-accumulated-attributes-conf
      - file: icinga-configuration-{{data.type}}-{{data.name}}-object-conf
{% endfor %}

{% endmacro %}



{% macro configuration_add_auto_host(hostname,
                                     attrs={},
                                     ssh_user='root',
                                     ssh_addr,
                                     ssh_port=22,
                                     check_ssh=True,
                                     mountpoint_root=True,
                                     mountpoint_var=False,
                                     mountpoint_srv=False,
                                     mountpoint_data=False,
                                     mountpoint_home=False,
                                     mountpoint_var_makina=False,
                                     mountpoint_var_www=False,
                                     check_mountpoints=True,
                                     check_http=True,
                                     check_cpuload=True
                                    ) %}
{% set data = salt['mc_icinga.add_auto_configuration_host_settings'](hostname,
                                                                     attrs,
                                                                     ssh_user,
                                                                     ssh_addr,
                                                                     ssh_port,
                                                                     check_ssh,
                                                                     mountpoint_root,
                                                                     mountpoint_var,
                                                                     mountpoint_srv,
                                                                     mountpoint_data,
                                                                     mountpoint_home,
                                                                     mountpoint_var_makina,
                                                                     mountpoint_var_www,
                                                                     check_mountpoints,
                                                                     check_http,
                                                                     check_cpuload,
                                                                     **kwargs
                                                                    ) %}
{% set sdata = salt['mc_utils.json_dump'](data) %}

# add the host object
{{ configuration_add_object(type='host',
                            file='hosts/'+data.hostname+'/host.cfg',
                            attrs=data.attrs) }}

# add a SSH service
{% if data.check_ssh %}
    {{ configuration_add_object(type='service',
                                file='hosts/'+data.hostname+'/ssh.cfg',
                                attrs= {
                                    'service_description': "SSH port "+ssh_port|string,
                                    'host_name': data.hostname,
                                    'use': "generic-service",
                                    'check_command': "check_ssh!"+ssh_port|string,
                                })
    }}
{% endif %}


# add mountpoints
{% if data.check_mountpoints %}
{% for mountpoint, path in data.mountpoints.items() %}
    {{ configuration_add_object(type='service',
                                file='hosts/'+data.hostname+'/'+mountpoint+'.cfg',
                                attrs= {
                                    'service_description': "Free space on "+path,
                                    'host_name': data.hostname,
                                    'use': "generic-service",
                                    'check_command': "check_by_ssh_mountpoint!"+ssh_user+"!"+ssh_addr+"!"+ssh_port|string+"!"+path+"!"+data.mountpoints_warning|string+"!"+data.mountpoints_critical|string,
                                })
    }}
{% endfor %}
{% endif %}

# add cpuload
{% if data.check_cpuload %}
    {{ configuration_add_object(type='service',
                                file='hosts/'+data.hostname+'/cpuload.cfg',
                                attrs= {
                                    'service_description': "Cpu load",
                                    'host_name': data.hostname,
                                    'use': "generic-service",
                                    'check_command': "check_by_ssh_cpuload!"+ssh_user+"!"+ssh_addr+"!"+ssh_port|string+"!"+data.cpuload_warning|string+"!"+data.cpuload_critical|string,
                                })
    }}
{% endif %}

# add http
{% if data.check_http %}
    {{ configuration_add_object(type='service',
                                file='hosts/'+data.hostname+'/http.cfg',
                                attrs= {
                                    'service_description': "HTTP",
                                    'host_name': data.hostname,
                                    'use': "generic-service",
                                    'check_command': "check_http",
                                })
    }}
{% endif %}
{% endmacro %}

