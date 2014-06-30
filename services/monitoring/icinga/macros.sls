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


{% macro configuration_add_auto_host(hostname, attrs={}, ssh_user) %}
{% set data = salt['mc_icinga.add_auto_configuration_host_settings'](hostname, attrs, ssh_user, **kwargs) %}
{% set sdata = salt['mc_utils.json_dump'](data) %}
{% set ssh_command = 'ssh -q '+data.ssh_user+'@'+data.attrs['address']+' ' %}

# we add the host object
{{ configuration_add_object(type='host',
                            file=data.hostname+'/host.cfg',
                            attrs=data.attrs) }}

# we connect to ssh and get the mc_localsettings.registry, mc_services.registry and grains
{% set host_services_registry = salt['cmd.run'](ssh_command+'salt-call --out=json mc_services.registry') %}
{% set host_localsettings_registry = salt['cmd.run'](ssh_command+'salt-call --out=json mc_localsettings.registry') %}
{% set host_grains = salt['cmd.run'](ssh_command+'salt-call --out=json grains.items') %}
# and transform str to json
{% set host_services_registry = salt['mc_utils.json_load'](host_services_registry) %}
{% set host_localsettings_registry = salt['mc_utils.json_load'](host_localsettings_registry) %}
{% set host_grains = salt['mc_utils.json_load'](host_grains) %}

# add a SSH service
{% if ( 'base.ssh' in host_services_registry.local.has
      and host_services_registry.local.has['base.ssh'] ) %}
    {% set ssh_port = salt['cmd.run'](ssh_command+'"grep -E \'^([ \t]*)Port\' /etc/ssh/sshd_config" | awk \'{print $2}\'') %}
    # python doesn't like
    {#{% set default_ssh_port =  salt['cmd.run']('sed -ne \'s#^ssh\([^0-9]\+\)\([0-9]*\)/tcp\(.*\)#\2#p\' /etc/services') %}#}
    {% set default_ssh_port = salt['cmd.run']('grep ssh /etc/services | awk \'{print $2}\' | grep tcp | awk -F \'/\' \'{print $1}\'') %}
    {% set ssh_port= default_ssh_port if (''==ssh_port) else ssh_port %}

    {{ configuration_add_object(type='service',
                            file=data.hostname+'/ssh.cfg',
                            attrs= {
                             'service_description': "SSH port "+ssh_port,
                             'host_name': data.hostname,
                             'use': "generic-service",
                             'check_command': "check_ssh!"+ssh_port,
                            }
       ) }}

{% endif %}

# add cpu loads
# the command should be modified in order to use nrpe or nsca
{% for cpu in range(host_grains.local.num_cpus) %}
    {{ configuration_add_object(type='service',
                            file=data.hostname+"/cpu_"+cpu|string+".cfg",
                            attrs= {
                             'service_description': "CPU_"+cpu|string+" load",
                             'host_name': data.hostname,
                             'use': "generic-service",
                             'check_command': "check_passive",
                            }
       ) }}

{% endfor %}

# add mountpoints service


# add http service
{% if ( ('http.apache' in host_services_registry.local.has
         and host_services_registry.local.has['http.apache'])
   or   ('http.apache_modfastcgi' in host_services_registry.local.has
         and host_services_registry.local.has['http.apache_modfastcgi'])
   or   ('http.apache_modfcgid' in host_services_registry.local.has
         and host_services_registry.local.has['http.apache_modfcgid'])
   or   ('http.apache_modproxy' in host_services_registry.local.has
         and host_services_registry.local.has['http.apache_modproxy'])
   or   ('http.nginx' in host_services_registry.local.has
         and host_services_registry.local.has['http.nginx'])
      ) %}

    {{ configuration_add_object(type='service',
                            file=data.hostname+'/http.cfg',
                            attrs= {
                             'service_description': "HTTP",
                             'host_name': data.hostname,
                             'use': "generic-service",
                             'check_command': "check_http",
                            }
       ) }}

{% endif %}

# add dns service
# the command should be modified. there is no check_dns command by default
{% for ip4 in host_grains.local.fqdn_ip4 %}
    # fqdn to ip4
    {{ configuration_add_object(type='service',
                            file=data.hostname+'/dns-ip4-'+host_grains.local.fqdn+'-'+ip4+'.cfg',
                            attrs= {
                             'service_description': "DNS for "+host_grains.local.fqdn+" → "+ip4,
                             'host_name': data.hostname,
                             'use': "generic-service",
                             'check_command': "check_passive",
                            }
       ) }}
    # ip4 to fqdn
    # think to translate a.b.c.d -> d.c.b.a.ip-addr.arpa.
    {{ configuration_add_object(type='service',
                            file=data.hostname+'/dns-ip4-'+ip4+'-'+host_grains.local.fqdn+'.cfg',
                            attrs= {
                             'service_description': "DNS for "+ip4+" → "+host_grains.local.fqdn,
                             'host_name': data.hostname,
                             'use': "generic-service",
                             'check_command': "check_passive",
                            }
       ) }}
{% endfor %}
{% for ip6 in host_grains.local.fqdn_ip6 %}
    # fqdn to ip6
    {{ configuration_add_object(type='service',
                            file=data.hostname+'/dns-ip6-'+host_grains.local.fqdn+'-'+ip6+'.cfg',
                            attrs= {
                             'service_description': "DNS for "+host_grains.local.fqdn+" → "+ip6,
                             'host_name': data.hostname,
                             'use': "generic-service",
                             'check_command': "check_passive",
                            }
       ) }}
    # ip6 to fqdn
    # think to translate a:b:c:d:e:f:g:h -> h.g.f.e.d.c.d.a.ip6.arpa.
    {{ configuration_add_object(type='service',
                            file=data.hostname+'/dns-ip6-'+ip6+'-'+host_grains.local.fqdn+'.cfg',
                            attrs= {
                             'service_description': "DNS for "+ip6+" → "+host_grains.local.fqdn,
                             'host_name': data.hostname,
                             'use': "generic-service",
                             'check_command': "check_passive",
                            }
       ) }}
{% endfor %}

# TODO: find ssh_port in grains or localsettings instead of using /etc/ssh/sshd_config
#       find mountpoints and storage devices from grains or localsettings
#       get http port and virtualhosts
#       add commands to check_dns

{% endmacro %}

