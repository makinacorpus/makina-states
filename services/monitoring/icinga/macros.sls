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

# we add the object
icinga-configuration-{{data.state_name_salt}}-object-conf:
  file.managed:
    - name: {{data.objects.directory}}/{{data.file}}
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
    - filename: {{data.objects.directory}}/{{data.file}}
    - text: "{{value_splitted}}"
    - watch:
      - mc_proxy: icinga-configuration-pre-accumulated-attributes-conf
    - watch_in:
      - mc_proxy: icinga-configuration-post-accumulated-attributes-conf
      - file: icinga-configuration-{{data.type}}-{{data.name}}-object-conf
{% endfor %}

{% endmacro %}


{#
#
# Macros mains args:
#     hostname
#         the hostname for the host to add
#     attrs
#         a dictionary in which each key corresponds to a directive in host definition
#     check_*
#         a boolean to indicate that the service has to be checked
#     ssh_user
#         user which is used to perform check_by_ssh
#     ssh_addr
#         address used to do the ssh connection in order to perform check_by_ssh
#         this address is not the hostname address becasue we can use a ssh gateway
#     ssh_port
#         ssh port
#     services_check_command_args
#         dictionary to override the arguments given in check_command for each service
#     html
#         dictionary to define vhost,url and a list of strings which must be found in the webpage
#
#}

{% macro configuration_add_auto_host(hostname,
                                     attrs={},
                                     ssh_user='root',
                                     ssh_addr,
                                     ssh_port=22,
                                     ssh_timeout=30,
                                     backup_burp_age=False,
                                     cron=False,
                                     ddos=false,
                                     debian_updates=False,
                                     dns_association=False,
                                     disk_space=False,
                                     disk_space_root=False,
                                     disk_space_var=False,
                                     disk_space_srv=False,
                                     disk_space_data=False,
                                     disk_space_home=False,
                                     disk_space_var_makina=False,
                                     disk_space_var_www=False,
                                     drbd=False,
                                     load_avg=False,
                                     memory=False,
                                     memory_hyperviseur=False,
                                     network=False,
                                     raid=False,
                                     swap=False,
                                     web_apache_status=False,
                                     web_public=False,
                                     services_check_command_args={}
                                    ) %}
{% set data = salt['mc_icinga.add_auto_configuration_host_settings'](hostname,
                                                                     attrs,
                                                                     ssh_user,
                                                                     ssh_addr,
                                                                     ssh_port,
                                                                     ssh_timeout,
                                                                     backup_burp_age,
                                                                     cron,
                                                                     ddos,
                                                                     debian_updates,
                                                                     dns_association,
                                                                     disk_space,
                                                                     disk_space_root,
                                                                     disk_space_var,
                                                                     disk_space_srv,
                                                                     disk_space_data,
                                                                     disk_space_home,
                                                                     disk_space_var_makina,
                                                                     disk_space_var_www,
                                                                     drbd,
                                                                     load_avg,
                                                                     memory,
                                                                     memory_hyperviseur,
                                                                     network,
                                                                     raid,
                                                                     swap,
                                                                     web_apache_status,
                                                                     web_public,
                                                                     services_check_command_args,
                                                                     **kwargs
                                                                    ) %}
{% set sdata = salt['mc_utils.json_dump'](data) %}
{% set check_by_ssh_params = data.ssh_user+"!"+data.ssh_addr+"!"+data.ssh_port|string+"!"+data.ssh_timeout|string %}


# add the host object
{{ configuration_add_object(type='host',
                            file='hosts/'+data.hostname+'/host.cfg',
                            attrs=data.attrs) }}


# add backup_burp_age service 
# TODO: edit command in order to allow customization in check_by_ssh
{% if data.backup_burp_age %}
    {{ configuration_add_object(type='service',
                                file='hosts/'+data.hostname+'/backup_burp_age.cfg',
                                attrs= {
                                    'service_description': "S_BACKUP_BURP_AGE",
                                    'host_name': data.hostname,
                                    'use': "ST_BACKUP_DAILY_ALERT",
                                    'check_command': "CSSH_BACKUP_BURP!"
                                                     +data.services_check_command_args.backup_burp_age.ssh_addr+"!"
                                                     +data.services_check_command_args.backup_burp_age.warning|string+"!"
                                                     +data.services_check_command_args.backup_burp_age.critical|string,
                                })
    }}
{% endif %}

# add cron service
# TODO: edit command in order to allow customization in check_by_ssh
{% if data.cron %}
    {{ configuration_add_object(type='service',
                                file='hosts/'+data.hostname+'/cron.cfg',
                                attrs= {
                                    'service_description': "S_PROC_CRON",
                                    'host_name': data.hostname,
                                    'use': "ST_SSH_PROC_CRON",
                                    'check_command': "CSSH_CRON"
                                })
    }}
{% endif %}

# add ddos service
# TODO: edit command in order to allow customization in check_by_ssh
{% if data.ddos %}
    {{ configuration_add_object(type='service',
                                file='hosts/'+data.hostname+'/ddos.cfg',
                                attrs= {
                                    'service_description': "DDOS",
                                    'host_name': data.hostname,
                                    'use': "ST_ALERT",
                                    'check_command': "CSSH_DDOS!"
                                                     +data.services_check_command_args.ddos.warning|string+"!"
                                                     +data.services_check_command_args.ddos.critical|string,
                                })
    }}
{% endif %}

# add debian_updates service
# TODO: edit command in order to allow customization in check_by_ssh
{% if data.debian_updates %}
    {{ configuration_add_object(type='service',
                                file='hosts/'+data.hostname+'/debian_updates.cfg',
                                attrs= {
                                    'service_description': "S_DEBIAN_UPDATES",
                                    'host_name': data.hostname,
                                    'use': "ST_DAILY_NOALERT",
                                    'check_command': "CSSH_DEBIAN_UPDATES"
                                })
    }}
{% endif %}

# add dns_association service 
{% if data.dns_association %}
    {% for name, dns_association in data.services_check_command_args.dns_association.items() %}
    {% if data.hostname == dns_association.hostname %}
        {% set use = "ST_DNS_ASSOCIATION_hostname" %}
    {% else %}
        {% set use = "ST_DNS_ASSOCIATION" %}
    {% endif %}
        {{ configuration_add_object(type='service',
                                    file='hosts/'+data.hostname+'/dns_association_'+name+'.cfg',
                                    attrs= {
                                        'service_description': "DNS_ASSOCIATION_"+dns_association.hostname,
                                        'host_name': data.hostname,
                                        'use': use,
                                        'check_command': "C_DNS_EXTERNE_ASSOCIATION!"
                                                         +dns_association.hostname+"!"
                                                         +dns_association.other_args,
                                    })
        }}
    {% endfor %}
{% endif %}

# add disk_space service
{% if data.disk_space %}
    {% for mountpoint, path in data.disks_spaces.items() %}
        {{ configuration_add_object(type='service',
                                    file='hosts/'+data.hostname+'/'+mountpoint+'.cfg',
                                    attrs= {
                                        'service_description': "DISK_SPACE_"+path,
                                        'host_name': data.hostname,
                                        'use': "ST_DISK_"+path,
                                        'icon_image': "services/nas3.png",
                                        'check_command': "C_SNMP_DISK!"
                                                         +path+"!"
                                                         +data.services_check_command_args.disk_space[mountpoint].warning|string+"!"
                                                         +data.services_check_command_args.disk_space[mountpoint].critical|string,
                                    })
        }}
    {% endfor %}
{% endif %}

# add drbd service
# TODO: edit command in order to allow customization in check_by_ssh
# TODO: add contact groups
{% if data.drbd %}
    {{ configuration_add_object(type='service',
                                file='hosts/'+data.hostname+'/drbd.cfg',
                                attrs= {
                                    'service_description': "CHECK_DRBD",
                                    'host_name': data.hostname,
                                    'use': "ST_ALERT",
                                    'check_command': "CSSH_DRBD!"
                                                     +data.services_check_command_args.drbd.command,
                                })
    }}
{% endif %}

# add load avg service
{% if data.load_avg %}
    {{ configuration_add_object(type='service',
                                file='hosts/'+data.hostname+'/load_avg.cfg',
                                attrs= {
                                    'service_description': "LOAD_AVG",
                                    'host_name': data.hostname,
                                    'use': "ST_LOAD_AVG",
                                    'check_command': "C_SNMP_LOADAVG!"
                                                     +data.services_check_command_args.load_avg.other_args,
                                })
    }}
{% endif %}

# add memory service
{% if data.memory %}
    {{ configuration_add_object(type='service',
                                file='hosts/'+data.hostname+'/memory.cfg',
                                attrs= {
                                    'service_description': "MEMORY",
                                    'host_name': data.hostname,
                                    'use': "ST_MEMORY",
                                    'check_command': "C_SNMP_MEMORY!"
                                                     +data.services_check_command_args.memory.warning|string+"!"
                                                     +data.services_check_command_args.memory.critical|string,
                                })
    }}
{% endif %}

# add memory_hyperviseur service
{% if data.memory_hyperviseur %}
    {{ configuration_add_object(type='service',
                                file='hosts/'+data.hostname+'/memory_hyperviseur.cfg',
                                attrs= {
                                    'service_description': "MEMORY_HYPERVISEUR",
                                    'host_name': data.hostname,
                                    'use': "ST_MEMORY_HYPERVISEUR",
                                    'check_command': "C_SNMP_MEMORY!"
                                                     +data.services_check_command_args.memory_hyperviseur.warning|string+"!"
                                                     +data.services_check_command_args.memory_hyperviseur.critical|string,
                                })
    }}
{% endif %}

# add network service
{% if data.network %}
    {% for name, network in data.services_check_command_args.network.items() %}
        {{ configuration_add_object(type='service',
                                    file='hosts/'+data.hostname+'/network_'+name+'.cfg',
                                    attrs= {
                                        'service_description': "NETWORK_"+network.interface,
                                        'host_name': data.hostname,
                                        'use': "ST_NETWORK_"+network.interface,
                                        'check_command': "C_SNMP_NETWORK!"
                                                         +network.interface+"!"
                                                         +network.other_args,
                                    })
        }}
    {% endfor %}
{% endif %}

# add raid service
# TODO: edit command in order to allow customization in check_by_ssh
{% if data.raid %}
    {{ configuration_add_object(type='service',
                                file='hosts/'+data.hostname+'/raid.cfg',
                                attrs= {
                                    'service_description': "CHECK_RAID",
                                    'host_name': data.hostname,
                                    'use': "ST_ALERT",
                                    'check_command': "CSSH_RAID_SOFT!"
                                                     +data.services_check_command_args.raid.command,
                                })
    }}
{% endif %}

# add swap service
# TODO: edit command in order to allow customization in check_by_ssh
{% if data.swap %}
    {{ configuration_add_object(type='service',
                                file='hosts/'+data.hostname+'/swap.cfg',
                                attrs= {
                                    'service_description': "CHECK_SWAP",
                                    'host_name': data.hostname,
                                    'use': "ST_ALERT",
                                    'check_command': "CSSH_RAID_SOFT!"
                                                     +data.services_check_command_args.swap.command,
                                })
    }}
{% endif %}

# add web apache status service
{% if data.web_apache_status %}
    {{ configuration_add_object(type='service',
                                file='hosts/'+data.hostname+'/web_apache_status.cfg',
                                attrs= {
                                    'service_description': "WEB_APACHE_STATUS",
                                    'host_name': data.hostname,
                                    'use': "ST_WEB_APACHE_STATUS",
                                    'check_command': "C_APACHE_STATUS!"
                                                     +data.services_check_command_args.web_apache_status.warning|string+"!"
                                                     +data.services_check_command_args.web_apache_status.critical|string+"!"
                                                     +data.services_check_command_args.web_apache_status.other_args,
                                })
    }}
{% endif %}

# add web_public_client service
# TODO: readd auth
{% if data.web_public %}
    {% for name, web_public in data.services_check_command_args.web_public.items() %}
        {% if 'antibug' == web_public.type %}
            {% set use = "ST_WEB_PUBLIC_antibug" %}
        {% else %}
            {% set use = "ST_WEB_PUBLIC_CLIENT" %}
        {% endif %}
        {{ configuration_add_object(type='service',
                                    file='hosts/'+data.hostname+'/web_public_'+name+'.cfg',
                                    attrs= {
                                        'service_description': "WEB_PUBLIC_"+name,
                                        'host_name': data.hostname,
                                        'use': use,
                                        'check_command': "C_HTTP_STRING!"
                                                         +web_public.hostname+"!"
                                                         +web_public.url+"!"
                                                         +web_public.warning|string+"!"
                                                         +web_public.critical|string+"!"
                                                         +web_public.timeout|string+"!"
                                                         +web_public.strings+"!"
                                                         +web_public.other_args,
                                    })
        }}
    {% endfor %}
{% endif %}

# FOR BACKUP (we adapt all services from centreon configuration)
{#
# add a SSH service
{% if data.check_ssh %}
    {{ configuration_add_object(type='service',
                                file='hosts/'+data.hostname+'/ssh.cfg',
                                attrs= {
                                    'service_description': "SSH "+data.services_check_command_args.ssh.hostname+" port "+data.services_check_command_args.ssh.port|string,
                                    'host_name': data.hostname,
                                    'use': "generic-service",
                                    'check_command': "check_ssh!"
                                                     +data.services_check_command_args.ssh.hostname+"!"
                                                     +data.services_check_command_args.ssh.port|string+"!"
                                                     +data.services_check_command_args.ssh.timeout|string
                                })
    }}
{% endif %}

{% if data.check_dns_reverse %}
    {{ configuration_add_object(type='service',
                                file='hosts/'+data.hostname+'/dns_reverse.cfg',
                                attrs= {
                                    'service_description': "DNS "+data.services_check_command_args.dns_reverse.query_address+" → "+data.services_check_command_args.dns_reverse.expected_address,
                                    'host_name': data.hostname,
                                    'use': "generic-service",
                                    'check_command': "check_dig!"
                                                     +data.services_check_command_args.dns_reverse.port|string+"!"
                                                     +data.services_check_command_args.dns_reverse.query_address+"!"
                                                     +data.services_check_command_args.dns_reverse.record_type+"!"
                                                     +data.services_check_command_args.dns_reverse.expected_address+"!"
                                                     +data.services_check_command_args.dns_reverse.timeout|string,
                                })
    }}
{% endif %}


# add http service
{% if data.check_http %}
    {{ configuration_add_object(type='service',
                                file='hosts/'+data.hostname+'/http.cfg',
                                attrs= {
                                    'service_description': "HTTP",
                                    'host_name': data.hostname,
                                    'use': "generic-service",
                                    'check_command': "check_http!"
                                                     +data.services_check_command_args.http.port|string+"!"
                                                     +data.services_check_command_args.http.hostname+"!"
                                                     +data.services_check_command_args.http.ip_address+"!"
                                                     +data.services_check_command_args.http.timeout|string,
                                })
    }}
{% endif %}


# add ntp peer service
{% if data.check_ntp_peer %}
    {{ configuration_add_object(type='service',
                                file='hosts/'+data.hostname+'/ntp_peer.cfg',
                                attrs= {
                                    'service_description': "NTP peer",
                                    'host_name': data.hostname,
                                    'use': "generic-service",
                                    'check_command': "check_ntp_peer!"
                                                     +data.services_check_command_args.ntp_peer.port|string+"!"
                                                     +data.services_check_command_args.ntp_peer.hostname+"!"
                                                     +data.services_check_command_args.ntp_peer.timeout|string,
                                })
    }}
{% endif %}

# add ntp time service (check by ssh)
{% if data.check_ntp_time %}
    {{ configuration_add_object(type='service',
                                file='hosts/'+data.hostname+'/ntp_time.cfg',
                                attrs= {
                                    'service_description': "NTP time",
                                    'host_name': data.hostname,
                                    'use': "generic-service",
                                    'check_command': "check_by_ssh_ntp_time!"
                                                     +check_by_ssh_params+"!"
                                                     +data.services_check_command_args.ntp_time.port|string+"!"
                                                     +data.services_check_command_args.ntp_time.hostname+"!"
                                                     +data.services_check_command_args.ntp_time.timeout|string,
                                })
    }}
{% endif %}


# add raid check (check by ssh)
{% if data.check_raid %}
    {{ configuration_add_object(type='service',
                                file='hosts/'+data.hostname+'/raid.cfg',
                                attrs= {
                                    'service_description': "Raid",
                                    'host_name': data.hostname,
                                    'use': "generic-service",
                                    'check_command': "check_by_ssh_raid!"
                                                     +check_by_ssh_params
                                })
    }}
{% endif %}

# add md_raid check (check by ssh)
{% if data.check_md_raid %}
    {{ configuration_add_object(type='service',
                                file='hosts/'+data.hostname+'/md_raid.cfg',
                                attrs= {
                                    'service_description': "md_raid",
                                    'host_name': data.hostname,
                                    'use': "generic-service",
                                    'check_command': "check_by_ssh_md_raid!"
                                                     +check_by_ssh_params
                                })
    }}
{% endif %}

# add megaraid_sas check (check by ssh)
{% if data.check_megaraid_sas %}
    {{ configuration_add_object(type='service',
                                file='hosts/'+data.hostname+'/megaraid_sas.cfg',
                                attrs= {
                                    'service_description': "megaraid sas",
                                    'host_name': data.hostname,
                                    'use': "generic-service",
                                    'check_command': "check_by_ssh_megaraid_sas!"
                                                     +check_by_ssh_params
                                })
    }}
{% endif %}

# add 3ware raid  service (check by ssh)
{% if data.check_drbd %}
    {{ configuration_add_object(type='service',
                                file='hosts/'+data.hostname+'/3ware_raid.cfg',
                                attrs= {
                                    'service_description': "3ware raid",
                                    'host_name': data.hostname,
                                    'use': "generic-service",
                                    'check_command': "check_by_ssh_3ware_raid!"
                                                     +check_by_ssh_params
                                })
    }}
{% endif %}

# add ccis service (check by ssh)
{% if data.check_cciss %}
    {{ configuration_add_object(type='service',
                                file='hosts/'+data.hostname+'/cciss.cfg',
                                attrs= {
                                    'service_description': "CCISS",
                                    'host_name': data.hostname,
                                    'use': "generic-service",
                                    'check_command': "check_by_ssh_cciss!"
                                                     +check_by_ssh_params
                                })
    }}
{% endif %}

# add drbd service (check by ssh)
{% if data.check_drbd %}
    {{ configuration_add_object(type='service',
                                file='hosts/'+data.hostname+'/drbd.cfg',
                                attrs= {
                                    'service_description': "Drbd",
                                    'host_name': data.hostname,
                                    'use': "generic-service",
                                    'check_command': "check_by_ssh_drbd!"
                                                     +check_by_ssh_params
                                })
    }}
{% endif %}




# add nb procs services (check by ssh)
{% if data.check_procs %}
    {{ configuration_add_object(type='service',
                                file='hosts/'+data.hostname+'/procs.cfg',
                                attrs= {
                                    'service_description': "Process",
                                    'host_name': data.hostname,
                                    'use': "generic-service",
                                    'check_command': "check_by_ssh_process!"
                                                     +check_by_ssh_params+"!"
                                                     +data.services_check_command_args.procs.metric+"!"
                                                     +data.services_check_command_args.procs.warning|string+"!"
                                                     +data.services_check_command_args.procs.critical|string,
                                })
    }}
{% endif %}

# add cron service (check by ssh)
{% if data.check_cron %}
    {{ configuration_add_object(type='service',
                                file='hosts/'+data.hostname+'/cron.cfg',
                                attrs= {
                                    'service_description': "Cron",
                                    'host_name': data.hostname,
                                    'use': "generic-service",
                                    'check_command': "check_by_ssh_cron!"
                                                     +check_by_ssh_params
                                })
    }}
{% endif %}

# add debian packages service (check by ssh)
{% if data.check_debian_packages %}
    {{ configuration_add_object(type='service',
                                file='hosts/'+data.hostname+'/debian_packages.cfg',
                                attrs= {
                                    'service_description': "Debian packages",
                                    'host_name': data.hostname,
                                    'use': "generic-service",
                                    'check_command': "check_by_ssh_debian_packages!"
                                                     +check_by_ssh_params
                                                     +data.services_check_command_args.debian_packages.timeout|string,
                                })
    }}
{% endif %}

# add solr service
{% if data.check_solr %}
    {{ configuration_add_object(type='service',
                                file='hosts/'+data.hostname+'/solr.cfg',
                                attrs= {
                                    'service_description': "Solr",
                                    'host_name': data.hostname,
                                    'use': "generic-service",
                                    'check_command': "check_solr!"
                                                     +data.services_check_command_args.solr.port|string+"!"
                                                     +data.services_check_command_args.solr.hostname+"!"
                                                     +data.services_check_command_args.solr.warning|string+"!"
                                                     +data.services_check_command_args.solr.critical|string+"!"
                                })
    }}
{% endif %}


# add rdiff backup age (check by ssh on the backup server)
{% if data.check_burp_backup_age %}
    {{ configuration_add_object(type='service',
                                file='hosts/'+data.hostname+'/rdiff.cfg',
                                attrs= {
                                    'service_description': "Rdiff backup age on "+data.services_check_command_args.rdiff.ssh_addr,
                                    'host_name': data.hostname,
                                    'use': "generic-service",
                                    'check_command': "check_by_ssh_rdiff!"
                                                     +data.services_check_command_args.rdiff.ssh_user+"!"
                                                     +data.services_check_command_args.rdiff.ssh_addr+"!"
                                                     +data.services_check_command_args.rdiff.ssh_port|string+"!"
                                                     +data.services_check_command_args.rdiff.ssh_timeout|string+"!"
                                                     +data.services_check_command_args.rdiff.repository+"!"
                                                     +data.services_check_command_args.rdiff.transferred_warning|string+"!"
                                                     +data.services_check_command_args.rdiff.cron_period|string+"!"
                                                     +data.services_check_command_args.rdiff.warning|string+"!"
                                                     +data.services_check_command_args.rdiff.critical|string,
                                })
    }}
{% endif %}



# add haproxy service (check by ssh)
{% if data.check_haproxy_stats %}
    {{ configuration_add_object(type='service',
                                file='hosts/'+data.hostname+'/haproxy_stats.cfg',
                                attrs= {
                                    'service_description': "haproxy stats",
                                    'host_name': data.hostname,
                                    'use': "generic-service",
                                    'check_command': "check_by_ssh_haproxy_stats!"
                                                     +check_by_ssh_params+"!"
                                                     +data.services_check_command_args.haproxy_stats.socket,
                                })
    }}
{% endif %}

# add postfix mailqueue service (check by ssh)
{% if data.check_postfixqueue %}
    {{ configuration_add_object(type='service',
                                file='hosts/'+data.hostname+'/postfixqueue.cfg',
                                attrs= {
                                    'service_description': "Postfix queue",
                                    'host_name': data.hostname,
                                    'use': "generic-service",
                                    'check_command': "check_by_ssh_postfixqueue!"
                                                     +check_by_ssh_params+"!"
                                                     +data.services_check_command_args.postfixqueue.warning|string+"!"
                                                     +data.services_check_command_args.postfixqueue.critical|string,
                                })
    }}
{% endif %}

# add postfix mail queue service (check by ssh)
{% if data.check_postfix_mailqueue %}
    {{ configuration_add_object(type='service',
                                file='hosts/'+data.hostname+'/postfix_mailqueue.cfg',
                                attrs= {
                                    'service_description': "Postfix mailqueue",
                                    'host_name': data.hostname,
                                    'use': "generic-service",
                                    'check_command': "check_by_ssh_postfix_mailqueue!"
                                                     +check_by_ssh_params
                                })
    }}
{% endif %}
#}
{% endmacro %}
