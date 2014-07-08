{# icinga2 macro helpers #}

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
{% set data = salt['mc_icinga2.add_configuration_object_settings'](type, file, attrs, **kwargs) %}
{% set sdata = salt['mc_utils.json_dump'](data) %}

# we add the object
icinga2-configuration-{{data.state_name_salt}}-object-conf:
  file.managed:
    - name: {{data.objects.directory}}/{{data.file}}
    - source: salt://makina-states/files/etc/icinga2/objects/template.cfg
    - user: root
    - group: root
    - mode: 644
    - makedirs: True
    - watch:
      - mc_proxy: icinga2-configuration-pre-object-conf
    - watch_in:
      - mc_proxy: icinga2-configuration-post-object-conf
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
{% set data = salt['mc_icinga2.edit_configuration_object_settings'](type, file, attr, value, **kwargs) %}
{% set sdata = salt['mc_utils.json_dump'](data) %}

# we split the value in ',' and loop. it is to remove duplicates values.
# for example, it is to avoid to produce "v1,v2,v1" if "v1,v2" are given in a call and "v1" in an other call
{% for value_splitted in data.value.split(',') %}
icinga2-configuration-{{data.state_name_salt}}-attribute-{{data.attr}}-{{value_splitted}}-conf:
  file.accumulated:
    - name: "{{data.attr}}"
    - filename: {{data.objects.directory}}/{{data.file}}
    - text: "{{value_splitted}}"
    - watch:
      - mc_proxy: icinga2-configuration-pre-accumulated-attributes-conf
    - watch_in:
      - mc_proxy: icinga2-configuration-post-accumulated-attributes-conf
      - file: icinga2-configuration-{{data.type}}-{{data.name}}-object-conf
{% endfor %}

{% endmacro %}


{#
#
# Macros mains args:
#     hostname
#         the hostname for the host to add
#     hostgroup
#         true if you want define a hostgroup instead of a host
#     attrs
#         a dictionary in which each key corresponds to a directive in host definition
#     check_*
#         a boolean to indicate that the service has to be checked
#     ssh_user
#         user which is used to perform check_by_ssh
#     ssh_addr
#         address used to do the ssh connection in order to perform check_by_ssh
#         this address is not the hostname address becasue we can use a ssh gateway
#         if empty: take the value given for "hostname"
#     ssh_port
#         ssh port
#     services_check_command_args
#         dictionary to override the arguments given in check_command for each service
#

# WILL BE REMOVED:
# for contacts and contact_groups, by default if no contact is given in services::
# If the contacts and contact_groups options are not set, it will notify host contacts instead

#}

{% macro configuration_add_auto_host(hostname,
                                     hostgroup=False,
                                     attrs={},
                                     ssh_user='root',
                                     ssh_addr='',
                                     ssh_port=22,
                                     ssh_timeout=30,
                                     backup_burp_age=False,
                                     backup_rdiff=False,
                                     beam_process=False,
                                     celeryd_process=False,
                                     cron=False,
                                     ddos=false,
                                     debian_updates=False,
                                     dns_association=False,
                                     dns_reverse_association=False,
                                     disk_space=False,
                                     disk_space_root=False,
                                     disk_space_var=False,
                                     disk_space_srv=False,
                                     disk_space_data=False,
                                     disk_space_home=False,
                                     disk_space_var_makina=False,
                                     disk_space_var_www=False,
                                     drbd=False,
                                     epmd_process=False,
                                     erp_files=False,
                                     fail2ban=False,
                                     gunicorn_process=False,
                                     haproxy=False,
                                     ircbot_process=False,
                                     load_avg=False,
                                     mail_cyrus_imap_connections=False,
                                     mail_imap=False,
                                     mail_imap_ssl=False,
                                     mail_pop=False,
                                     mail_pop_ssl=False,
                                     mail_pop_test_account=False,
                                     mail_server_queues=False,
                                     mail_smtp=False,
                                     md_raid=False,
                                     megaraid_sas=False,
                                     memory=False,
                                     memory_hyperviseur=False,
                                     mysql_process=False,
                                     network=False,
                                     ntp_peers=False,
                                     ntp_time=False,
                                     only_one_nagios_running=False,
                                     postgres_port=False,
                                     postgres_process=False,
                                     prebill_sending=False,
                                     raid=False,
                                     sas=False,
                                     snmpd_memory_control=False,
                                     solr=False,
                                     ssh=False,
                                     supervisord_status=False,
                                     swap=False,
                                     tiles_generator_access=False,
                                     ware_raid=False,
                                     web_apache_status=False,
                                     web_openid=False,
                                     web=False,
                                     services_check_command_args={}
                                    ) %}
{% set data = salt['mc_icinga2.add_auto_configuration_host_settings'](hostname,
                                                                     hostgroup,
                                                                     attrs,
                                                                     ssh_user,
                                                                     ssh_addr,
                                                                     ssh_port,
                                                                     ssh_timeout,
                                                                     backup_burp_age,
                                                                     backup_rdiff,
                                                                     beam_process,
                                                                     celeryd_process,
                                                                     cron,
                                                                     ddos,
                                                                     debian_updates,
                                                                     dns_association,
                                                                     dns_reverse_association,
                                                                     disk_space,
                                                                     disk_space_root,
                                                                     disk_space_var,
                                                                     disk_space_srv,
                                                                     disk_space_data,
                                                                     disk_space_home,
                                                                     disk_space_var_makina,
                                                                     disk_space_var_www,
                                                                     drbd,
                                                                     epmd_process,
                                                                     erp_files,
                                                                     fail2ban,
                                                                     gunicorn_process,
                                                                     haproxy,
                                                                     ircbot_process,
                                                                     load_avg,
                                                                     mail_cyrus_imap_connections,
                                                                     mail_imap,
                                                                     mail_imap_ssl,
                                                                     mail_pop,
                                                                     mail_pop_ssl,
                                                                     mail_pop_test_account,
                                                                     mail_server_queues,
                                                                     mail_smtp,
                                                                     md_raid,
                                                                     megaraid_sas,
                                                                     memory,
                                                                     memory_hyperviseur,
                                                                     mysql_process,
                                                                     network,
                                                                     ntp_peers,
                                                                     ntp_time,
                                                                     only_one_nagios_running,
                                                                     postgres_port,
                                                                     postgres_process,
                                                                     prebill_sending,
                                                                     raid,
                                                                     sas,
                                                                     snmpd_memory_control,
                                                                     solr,
                                                                     ssh,
                                                                     supervisord_status,
                                                                     swap,
                                                                     tiles_generator_access,
                                                                     ware_raid,
                                                                     web_apache_status,
                                                                     web_openid,
                                                                     web,
                                                                     services_check_command_args,
                                                                     **kwargs
                                                                    ) %}
{% set sdata = salt['mc_utils.json_dump'](data) %}
{% set check_by_ssh_params = data.ssh_user+"!"+data.ssh_addr+"!"+data.ssh_port|string+"!"+data.ssh_timeout|string %}

# add the host/hostgroup object
{{ configuration_add_object(type=data.type,
                            file=data.service_subdirectory+'/'+data.hostname+'/'+data.type+'.cfg',
                            attrs=data.attrs) }}


# add backup_burp_age service 
# TODO/ok: edit command in order to allow customization in check_by_ssh
{% if data.backup_burp_age %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/backup_burp_age.cfg',
                                attrs= {
                                    'service_description': "S_BACKUP_BURP_AGE",
                                    data.service_key_hostname: data.hostname,
                                    'use': "ST_BACKUP_DAILY_ALERT",
                                    'check_command': "CSSH_BACKUP_BURP!"
                                                     +data.services_check_command_args.backup_burp_age.ssh_user+"!"
                                                     +data.services_check_command_args.backup_burp_age.ssh_addr+"!"
                                                     +data.services_check_command_args.backup_burp_age.ssh_port|string+"!"
                                                     +data.services_check_command_args.backup_burp_age.ssh_timeout|string+"!"
                                                     +data.services_check_command_args.backup_burp_age.warning|string+"!"
                                                     +data.services_check_command_args.backup_burp_age.critical|string,
                                })
    }}
{% endif %}

# add backup_rdiff service
# TODO/ok: edit command in order to allow customization in check_by_ssh
{% if data.backup_rdiff %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/backup_rdiff.cfg',
                                attrs= {
                                    'service_description': "S_BACKUP_RDIFF",
                                    data.service_key_hostname: data.hostname,
                                    'use': "ST_BACKUP_DAILY_ALERT",
                                    'check_command': "CSSH_BACKUP!"
                                                     +data.services_check_command_args.backup_rdiff.ssh_user+"!"
                                                     +data.services_check_command_args.backup_rdiff.ssh_addr+"!"
                                                     +data.services_check_command_args.backup_rdiff.ssh_port|string+"!"
                                                     +data.services_check_command_args.backup_rdiff.ssh_timeout|string+"!"
                                                     +data.services_check_command_args.backup_rdiff.command,
                                })
    }}
{% endif %}

# add beam_process service
{% if data.beam_process %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/beam_process.cfg',
                                attrs= {
                                    'service_description': "Check beam process",
                                    data.service_key_hostname: data.hostname,
                                    'use': "ST_ALERT",
                                    'notification_options': "w,c,r",
                                    'notifications_enabled': 1,
                                    'check_command': "C_SNMP_PROCESS!"
                                                     +data.services_check_command_args.beam_process.process+"!"
                                                     +data.services_check_command_args.beam_process.warning|string+"!"
                                                     +data.services_check_command_args.beam_process.critical|string,
                                })
    }}
{% endif %}

# add celeryd_process service
{% if data.celeryd_process %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/celeryd_process.cfg',
                                attrs= {
                                    'service_description': "Check celeryd process",
                                    data.service_key_hostname: data.hostname,
                                    'use': "ST_ALERT",
                                    'notification_options': "w,c,r",
                                    'notifications_enabled': 1,
                                    'check_command': "C_SNMP_PROCESS!"
                                                     +data.services_check_command_args.celeryd_process.process+"!"
                                                     +data.services_check_command_args.celeryd_process.warning|string+"!"
                                                     +data.services_check_command_args.celeryd_process.critical|string,
                                })
    }}
{% endif %}

# add cron service
# TODO/ok: edit command in order to allow customization in check_by_ssh
{% if data.cron %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/cron.cfg',
                                attrs= {
                                    'service_description': "S_PROC_CRON",
                                    data.service_key_hostname: data.hostname,
                                    'use': "ST_SSH_PROC_CRON",
                                    'check_command': "CSSH_CRON!"
                                                     +check_by_ssh_params,
                                })
    }}
{% endif %}

# add ddos service
# TODO/ok: edit command in order to allow customization in check_by_ssh
{% if data.ddos %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/ddos.cfg',
                                attrs= {
                                    'service_description': "DDOS",
                                    data.service_key_hostname: data.hostname,
                                    'use': "ST_ALERT",
                                    'check_command': "CSSH_DDOS!"
                                                     +check_by_ssh_params+"!"
                                                     +data.services_check_command_args.ddos.warning|string+"!"
                                                     +data.services_check_command_args.ddos.critical|string,
                                })
    }}
{% endif %}

# add debian_updates service
# TODO/ok: edit command in order to allow customization in check_by_ssh
{% if data.debian_updates %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/debian_updates.cfg',
                                attrs= {
                                    'service_description': "S_DEBIAN_UPDATES",
                                    data.service_key_hostname: data.hostname,
                                    'use': "ST_DAILY_NOALERT",
                                    'check_command': "CSSH_DEBIAN_UPDATES!"
                                                     +check_by_ssh_params,
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
                                    file=data.service_subdirectory+'/'+data.hostname+'/dns_association_'+name+'.cfg',
                                    attrs= {
                                        'service_description': "DNS_ASSOCIATION_"+dns_association.hostname,
                                        data.service_key_hostname: data.hostname,
                                        'use': use,
                                        'check_command': "C_DNS_EXTERNE_ASSOCIATION!"
                                                         +dns_association.hostname+"!"
                                                         +dns_association.other_args,
                                    })
        }}
    {% endfor %}
{% endif %}

# add dns_reverse_association service
{% if data.dns_reverse_association %}
    {% for name, dns_association in data.services_check_command_args.dns_association.items() %}
    {% if data.hostname == dns_association.hostname %}
        {% set use = "ST_DNS_ASSOCIATION_hostname" %}
    {% else %}
        {% set use = "ST_DNS_ASSOCIATION" %}
    {% endif %}
        {{ configuration_add_object(type='service',
                                    file=data.service_subdirectory+'/'+data.hostname+'/dns_reverse_association_'+name+'.cfg',
                                    attrs= {
                                        'service_description': "DNS_REVERSE_ASSOCIATION_"+dns_association.hostname,
                                        data.service_key_hostname: data.hostname,
                                        'use': use,
                                        'check_command': "C_DNS_EXTERNE_REVERSE_ASSOCIATION!"
                                                         +dns_association.inaddr+"!"
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
                                    file=data.service_subdirectory+'/'+data.hostname+'/'+mountpoint+'.cfg',
                                    attrs= {
                                        'service_description': "DISK_SPACE_"+path,
                                        data.service_key_hostname: data.hostname,
                                        'use': "ST_DISK_SPACE_"+path|upper,
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
# TODO/ok: edit command in order to allow customization in check_by_ssh
# TODO: add contact groups
{% if data.drbd %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/drbd.cfg',
                                attrs= {
                                    'service_description': "CHECK_DRBD",
                                    data.service_key_hostname: data.hostname,
                                    'use': "ST_ALERT",
                                    'check_command': "CSSH_DRBD!"
                                                     +check_by_ssh_params+"!"
                                                     +data.services_check_command_args.drbd.command,
                                })
    }}
{% endif %}

# add epmd_process service
{% if data.epmd_process %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/epmd_process.cfg',
                                attrs= {
                                    'service_description': "Check epmd process",
                                    data.service_key_hostname: data.hostname,
                                    'use': "ST_ALERT",
                                    'notification_options': "w,c,r",
                                    'notifications_enabled': 1,
                                    'check_command': "C_SNMP_PROCESS!"
                                                     +data.services_check_command_args.epmd_process.process+"!"
                                                     +data.services_check_command_args.epmd_process.warning|string+"!"
                                                     +data.services_check_command_args.epmd_process.critical|string,
                                })
    }}
{% endif %}

# add erp_files service
# TODO/ok: edit command in order to allow customization in check_by_ssh
# TODO: add contact groups
{% if data.erp_files %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/erp_files.cfg',
                                attrs= {
                                    'service_description': "CHECK_ERP_FILES",
                                    data.service_key_hostname: data.hostname,
                                    'use': "ST_ALERT",
                                    'check_command': "CSSH_CUSTOM!"
                                                     +check_by_ssh_params+"!"
                                                     +data.services_check_command_args.erp_files.command,
                                })
    }}
{% endif %}

# add fail2ban service
{% if data.fail2ban %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/fail2ban.cfg',
                                attrs= {
                                    'service_description': "S_FAIL2BAN",
                                    data.service_key_hostname: data.hostname,
                                    'use': "ST_ROOT",
                                    'notifications_enabled': 1,
                                    'check_command': "C_SNMP_PROCESS!"
                                                     +data.services_check_command_args.fail2ban.process+"!"
                                                     +data.services_check_command_args.fail2ban.warning|string+"!"
                                                     +data.services_check_command_args.fail2ban.critical|string,
                                })
    }}
{% endif %}

# add gunicorn_process service
{% if data.gunicorn_process %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/gunicorn_process.cfg',
                                attrs= {
                                    'service_description': "Check gunicorn process",
                                    data.service_key_hostname: data.hostname,
                                    'use': "ST_ALERT",
                                    'notification_options': "w,c,r",
                                    'notifications_enabled': 1,
                                    'check_command': "C_SNMP_PROCESS!"
                                                     +data.services_check_command_args.gunicorn_process.process+"!"
                                                     +data.services_check_command_args.gunicorn_process.warning|string+"!"
                                                     +data.services_check_command_args.gunicorn_process.critical|string,
                                })
    }}
{% endif %}

# add haproxy service
{% if data.haproxy %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/haproxy.cfg',
                                attrs= {
                                    'service_description': "haproxy stats",
                                    data.service_key_hostname: data.hostname,
                                    'use': "ST_ALERT",
                                    'check_command': "CSSH_HAPROXY!"
                                                     +check_by_ssh_params+"!"
                                                     +data.services_check_command_args.haproxy.command,
                                })
    }}
{% endif %}

# add ircbot_process service
{% if data.ircbot_process %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/ircbot_process.cfg',
                                attrs= {
                                    'service_description': "S_IRCBOT_PROCESS",
                                    data.service_key_hostname: data.hostname,
                                    'use': "ST_HOURLY_ALERT",
                                    'check_command': "C_PROCESS_IRCBOT_RUNNING",
                                })
    }}
{% endif %}

# add load avg service
{% if data.load_avg %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/load_avg.cfg',
                                attrs= {
                                    'service_description': "LOAD_AVG",
                                    data.service_key_hostname: data.hostname,
                                    'use': "ST_LOAD_AVG",
                                    'check_command': "C_SNMP_LOADAVG!"
                                                     +data.services_check_command_args.load_avg.other_args,
                                })
    }}
{% endif %}

# add mail_cyrus_imap_connections service
# TODO/ok: edit command in order to allow customization in check_by_ssh
{% if data.mail_cyrus_imap_connections %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/mail_cyrus_imap_connections.cfg',
                                attrs= {
                                    'service_description': "S_MAIL_CYRUS_IMAP_CONNECTIONS",
                                    data.service_key_hostname: data.hostname,
                                    'use': "ST_ALERT",
                                    'check_command': "CSSH_CYRUS_CONNECTIONS!"
                                                     +check_by_ssh_params+"!"
                                                     +data.services_check_command_args.mail_cyrus_imap_connections.warning|string+"!"
                                                     +data.services_check_command_args.mail_cyrus_imap_connections.critical|string,
                                })
    }}
{% endif %}

# add mail_imap service
{% if data.mail_imap %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/mail_imap.cfg',
                                attrs= {
                                    'service_description': "S_MAIL_IMAP",
                                    data.service_key_hostname: data.hostname,
                                    'use': "ST_ALERT",
                                    'check_command': "C_MAIL_IMAP!"
                                                     +data.services_check_command_args.mail_imap.warning|string+"!"
                                                     +data.services_check_command_args.mail_imap.critical|string,
                                })
    }}
{% endif %}

# add mail_imap_ssl service
{% if data.mail_imap_ssl %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/mail_imap_ssl.cfg',
                                attrs= {
                                    'service_description': "S_MAIL_IMAP_SSL",
                                    data.service_key_hostname: data.hostname,
                                    'use': "ST_ALERT",
                                    'check_command': "C_MAIL_IMAP_SSL!"
                                                     +data.services_check_command_args.mail_imap_ssl.warning|string+"!"
                                                     +data.services_check_command_args.mail_imap_ssl.critical|string,
                                })
    }}
{% endif %}

# add mail_pop service
{% if data.mail_pop %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/mail_pop.cfg',
                                attrs= {
                                    'service_description': "S_MAIL_POP",
                                    data.service_key_hostname: data.hostname,
                                    'use': "ST_ALERT",
                                    'check_command': "C_MAIL_POP!"
                                                     +data.services_check_command_args.mail_pop.warning|string+"!"
                                                     +data.services_check_command_args.mail_pop.critical|string,
                                })
    }}
{% endif %}

# add mail_pop_ssl service
{% if data.mail_pop_ssl %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/mail_pop_ssl.cfg',
                                attrs= {
                                    'service_description': "S_MAIL_POP_SSL",
                                    data.service_key_hostname: data.hostname,
                                    'use': "ST_ALERT",
                                    'check_command': "C_MAIL_POP_SSL!"
                                                     +data.services_check_command_args.mail_pop_ssl.warning|string+"!"
                                                     +data.services_check_command_args.mail_pop_ssl.critical|string,
                                })
    }}
{% endif %}

# add mail_pop_test_account service
{% if data.mail_pop_test_account %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/mail_pop_test_account.cfg',
                                attrs= {
                                    'service_description': "S_MAIL_POP3_TEST_ACCOUNT",
                                    data.service_key_hostname: data.hostname,
                                    'use': "ST_ALERT",
                                    'check_command': "C_POP3_TEST_SIZE_AND_DELETE!"
                                                     +data.services_check_command_args.mail_pop_test_account.warning1|string+"!"
                                                     +data.services_check_command_args.mail_pop_test_account.critical1|string+"!"
                                                     +data.services_check_command_args.mail_pop_test_account.warning2|string+"!"
                                                     +data.services_check_command_args.mail_pop_test_account.critical2|string+"!"
                                                     +data.services_check_command_args.mail_pop_test_account.mx,
                                })
    }}
{% endif %}

# add mail_server_queues service
# TODO/ok: edit command in order to allow customization in check_by_ssh
{% if data.mail_server_queues %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/mail_server_queues.cfg',
                                attrs= {
                                    'service_description': "S_MAIL_SERVER_QUEUES",
                                    data.service_key_hostname: data.hostname,
                                    'use': "ST_ALERT",
                                    'check_command': "CSSH_MAILQUEUE!"
                                                     +check_by_ssh_params+"!"
                                                     +data.services_check_command_args.mail_server_queues.warning|string+"!"
                                                     +data.services_check_command_args.mail_server_queues.critical|string,
                                })
    }}
{% endif %}

# add mail_smtp service
{% if data.mail_smtp %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/mail_smtp.cfg',
                                attrs= {
                                    'service_description': "S_MAIL_SMTP",
                                    data.service_key_hostname: data.hostname,
                                    'use': "ST_ALERT",
                                    'check_command': "C_MAIL_SMTP!"
                                                     +data.services_check_command_args.mail_smtp.warning|string+"!"
                                                     +data.services_check_command_args.mail_smtp.critical|string,
                                })
    }}
{% endif %}

# add md_raid service
# TODO/ok: edit command in order to allow customization in check_by_ssh
{% if data.md_raid %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/md_raid.cfg',
                                attrs= {
                                    'service_description': "CHECK_MD_RAID",
                                    data.service_key_hostname: data.hostname,
                                    'use': "ST_ALERT",
                                    'check_command': "CSSH_RAID_SOFT!"
                                                     +check_by_ssh_params+"!"
                                                     +data.services_check_command_args.md_raid.command,
                                })
    }}
{% endif %}

# add megaraid_sas service
{% if data.megaraid_sas %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/megaraid_sas.cfg',
                                attrs= {
                                    'service_description': "CHECK_MEGARAID_SAS",
                                    data.service_key_hostname: data.hostname,
                                    'use': "ST_ALERT",
                                    'check_command': "CSSH_MEGARAID_SAS!"
                                                     +check_by_ssh_params+"!"
                                                     +data.services_check_command_args.megaraid_sas.command,
                                })
    }}
{% endif %}

# add memory service
{% if data.memory %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/memory.cfg',
                                attrs= {
                                    'service_description': "MEMORY",
                                    data.service_key_hostname: data.hostname,
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
                                file=data.service_subdirectory+'/'+data.hostname+'/memory_hyperviseur.cfg',
                                attrs= {
                                    'service_description': "MEMORY_HYPERVISEUR",
                                    data.service_key_hostname: data.hostname,
                                    'use': "ST_MEMORY_HYPERVISEUR",
                                    'check_command': "C_SNMP_MEMORY!"
                                                     +data.services_check_command_args.memory_hyperviseur.warning|string+"!"
                                                     +data.services_check_command_args.memory_hyperviseur.critical|string,
                                })
    }}
{% endif %}

# add mysql_process service
{% if data.mysql_process %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/mysql_process.cfg',
                                attrs= {
                                    'service_description': "S_MYSQL_PROCESS",
                                    data.service_key_hostname: data.hostname,
                                    'use': "ST_ALERT",
                                    'check_command': "C_SNMP_PROCESS!"
                                                     +data.services_check_command_args.mysql_process.process+"!"
                                                     +data.services_check_command_args.mysql_process.warning|string+"!"
                                                     +data.services_check_command_args.mysql_process.critical|string,
                                })
    }}
{% endif %}

# add network service
{% if data.network %}
    {% for name, network in data.services_check_command_args.network.items() %}
        {{ configuration_add_object(type='service',
                                    file=data.service_subdirectory+'/'+data.hostname+'/network_'+name+'.cfg',
                                    attrs= {
                                        'service_description': "NETWORK_"+network.interface,
                                        data.service_key_hostname: data.hostname,
                                        'use': "ST_NETWORK_"+network.interface|upper,
                                        'check_command': "C_SNMP_NETWORK!"
                                                         +network.interface+"!"
                                                         +network.other_args,
                                    })
        }}
    {% endfor %}
{% endif %}

# add ntp_peers service
# TODO/ok: cssh
{% if data.ntp_peers %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/ntp_peers.cfg',
                                attrs= {
                                    'service_description': "S_NTP_PEERS",
                                    data.service_key_hostname: data.hostname,
                                    'use': "ST_ROOT",
                                    'check_command': "CSSH_NTP_PEER!"
                                                     +check_by_ssh_params,
                                })
    }}
{% endif %}

# add ntp_time service
# TODO/ok: cssh
{% if data.ntp_time %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/ntp_time.cfg',
                                attrs= {
                                    'service_description': "S_NTP_TIME",
                                    data.service_key_hostname: data.hostname,
                                    'use': "ST_ROOT",
                                    'check_command': "CSSH_NTP_TIME!"
                                                     +check_by_ssh_params,
                                })
    }}
{% endif %}

# add only_one_nagios_running service
{% if data.only_one_nagios_running %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/only_one_nagios_running.cfg',
                                attrs= {
                                    'service_description': "S_ONLY_ONE_NAGIOS_RUNNING",
                                    data.service_key_hostname: data.hostname,
                                    'use': "ST_HOURLY_ALERT",
                                    'check_command': "C_CHECK_ONE_NAGIOS_ONLY"
                                })
    }}
{% endif %}

# add postgres_port service
{% if data.postgres_port %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/postgres_port.cfg',
                                attrs= {
                                    'service_description': "S_POSTGRESQL_PORT",
                                    data.service_key_hostname: data.hostname,
                                    'use': "ST_ROOT",
                                    'check_command': "check_tcp!"
                                                     +data.services_check_command_args.postgres_port.port|string+"!"
                                                     +data.services_check_command_args.postgres_port.warning|string+"!"
                                                     +data.services_check_command_args.postgres_port.critical|string,
                                })
    }}
{% endif %}

# add postgres_process service
{% if data.postgres_process %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/postgres_process.cfg',
                                attrs= {
                                    'service_description': "Check postgres process",
                                    data.service_key_hostname: data.hostname,
                                    'use': "ST_ALERT",
                                    'notification_options': "w,c,r",
                                    'notifications_enabled': 1,
                                    'check_command': "C_SNMP_PROCESS!"
                                                     +data.services_check_command_args.postgres_process.process+"!"
                                                     +data.services_check_command_args.postgres_process.warning|string+"!"
                                                     +data.services_check_command_args.postgres_process.critical|string,
                                })
    }}
{% endif %}

# add prebill_sending service
# TODO/ok: edit command in order to allow customization in check_by_ssh
{% if data.prebill_sending %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/prebill_sending.cfg',
                                attrs= {
                                    'service_description': "CHECK_PREBILL_SENDING",
                                    data.service_key_hostname: data.hostname,
                                    'use': "ST_ALERT",
                                    'check_command': "CSSH_CUSTOM!"
                                                     +check_by_ssh_params+"!"
                                                     +data.services_check_command_args.prebill_sending.command,
                                })
    }}
{% endif %}

# add raid service
# TODO/ok: edit command in order to allow customization in check_by_ssh
{% if data.raid %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/raid.cfg',
                                attrs= {
                                    'service_description': "CHECK_RAID",
                                    data.service_key_hostname: data.hostname,
                                    'use': "ST_ALERT",
                                    'check_command': "CSSH_RAID_SOFT!"
                                                     +check_by_ssh_params+"!"
                                                     +data.services_check_command_args.raid.command,
                                })
    }}
{% endif %}

# add sas service
# TODO/ok: edit command in order to allow customization in check_by_ssh
{% if data.raid %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/sas.cfg',
                                attrs= {
                                    'service_description': "S_SAS",
                                    data.service_key_hostname: data.hostname,
                                    'use': "ST_ROOT",
                                    'check_command': "CSSH_SAS2IRCU!"
                                                     +check_by_ssh_params+"!"
                                                     +data.services_check_command_args.sas.command,
                                })
    }}
{% endif %}

# add snmpd_memory_control service
{% if data.raid %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/snmpd_memory_control.cfg',
                                attrs= {
                                    'service_description': "S_SNMPD_MEMORY_CONTROL",
                                    data.service_key_hostname: data.hostname,
                                    'use': "ST_ALERT",
                                    'check_command': "C_SNMP_PROCESS_WITH_MEM!"
                                                     +data.services_check_command_args.snmpd_memory_control.process+"!"
                                                     +data.services_check_command_args.snmpd_memory_control.warning+"!"
                                                     +data.services_check_command_args.snmpd_memory_control.critical+"!"
                                                     +data.services_check_command_args.snmpd_memory_control.memory,
                                })
    }}
{% endif %}

# add solr service
# TODO: readd auth
{% if data.solr %}
    {% for name, solr in data.services_check_command_args.solr.items() %}
        {{ configuration_add_object(type='service',
                                    file=data.service_subdirectory+'/'+data.hostname+'/solr_'+name+'.cfg',
                                    attrs= {
                                        'service_description': "SOLR_"+name,
                                        data.service_key_hostname: data.hostname,
                                        'use': "ST_WEB_PUBLIC",
                                        'check_command': "C_HTTP_STRING_SOLR!"
                                                         +solr.hostname+"!"
                                                         +solr.port|string+"!"
                                                         +solr.url+"!"
                                                         +solr.warning|string+"!"
                                                         +solr.critical|string+"!"
                                                         +solr.timeout|string+"!"
                                                         +solr.strings+"!"
                                                         +solr.other_args,
                                    })
        }}
    {% endfor %}
{% endif %}

# add ssh service
{% if data.ssh %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/ssh.cfg',
                                attrs= {
                                    'service_description': "S_SSH",
                                    data.service_key_hostname: data.hostname,
                                    'use': "ST_ROOT",
                                    'check_command': "check_tcp!"
                                                     +data.services_check_command_args.ssh.port|string+"!"
                                                     +data.services_check_command_args.ssh.warning|string+"!"
                                                     +data.services_check_command_args.ssh.critical|string
                                })
    }}
{% endif %}

# add supervisord_status service
# TODO/ok: edit command in order to allow customization in check_by_ssh
{% if data.supervisord_status %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/supervisord_status.cfg',
                                attrs= {
                                    'service_description': "S_SUPERVISORD_STATUS",
                                    data.service_key_hostname: data.hostname,
                                    'use': "ST_ALERT",
                                    'check_command': "CSSH_SUPERVISOR!"
                                                     +check_by_ssh_params+"!"
                                                     +data.services_check_command_args.supervisord_status.command,
                                })
    }}
{% endif %}

# add swap service
# TODO/ok: edit command in order to allow customization in check_by_ssh
{% if data.swap %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/swap.cfg',
                                attrs= {
                                    'service_description': "CHECK_SWAP",
                                    data.service_key_hostname: data.hostname,
                                    'use': "ST_ALERT",
                                    'check_command': "CSSH_RAID_SOFT!"
                                                     +check_by_ssh_params+"!"
                                                     +data.services_check_command_args.swap.command,
                                })
    }}
{% endif %}

# add tiles_generator_access service
{% if data.tiles_generator_access %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/tiles_generator_access.cfg',
                                attrs= {
                                    'service_description': "Check tiles generator access",
                                    data.service_key_hostname: data.hostname,
                                    'use': "ST_ALERT",
                                    'notification_options': "w,c,r",
                                    'notifications_enabled': 1,
                                    'check_command': "check_http_vhost_uri!"
                                                     +data.services_check_command_args.tiles_generator_access.hostname+"!"
                                                     +data.services_check_command_args.tiles_generator_access.url,
                                })
    }}
{% endif %}

# add 3ware raid  service (check by ssh)
{% if data.ware_raid %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/3ware_raid.cfg',
                                attrs= {
                                    'service_description': "CHECK_3WARE_RAID",
                                    data.service_key_hostname: data.hostname,
                                    'use': "ST_ALERT",
                                    'check_command': "CSSH_RAID_3WARE!"
                                                     +check_by_ssh_params+"!"
                                                     +data.services_check_command_args.ware_raid.command,
                                })
    }}
{% endif %}

# add web apache status service
{% if data.web_apache_status %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/web_apache_status.cfg',
                                attrs= {
                                    'service_description': "WEB_APACHE_STATUS",
                                    data.service_key_hostname: data.hostname,
                                    'use': "ST_WEB_APACHE_STATUS",
                                    'check_command': "C_APACHE_STATUS!"
                                                     +data.services_check_command_args.web_apache_status.warning|string+"!"
                                                     +data.services_check_command_args.web_apache_status.critical|string+"!"
                                                     +data.services_check_command_args.web_apache_status.other_args,
                                })
    }}
{% endif %}

# add web_openid service
# TODO: readd auth
{% if data.web_openid %}
    {% for name, web_openid in data.services_check_command_args.web_openid.items() %}
        {{ configuration_add_object(type='service',
                                    file=data.service_subdirectory+'/'+data.hostname+'/web_openid_'+name+'.cfg',
                                    attrs= {
                                        'service_description': "WEB_OPENID_"+name,
                                        data.service_key_hostname: data.hostname,
                                        'use': "ST_WEB_PUBLIC",
                                        'check_command': "C_HTTPS_OPENID_REDIRECT!"
                                                         +web_openid.hostname+"!"
                                                         +web_openid.url+"!"
                                                         +web_openid.warning|string+"!"
                                                         +web_openid.critical|string+"!"
                                                         +web_openid.timeout|string,
                                    })
        }}
    {% endfor %}
{% endif %}

# add web service
# TODO/ok: readd auth
{% if data.web %}
    {% for name, web in data.services_check_command_args.web.items() %}
        {{ configuration_add_object(type='service',
                                    file=data.service_subdirectory+'/'+data.hostname+'/web_'+name+'.cfg',
                                    attrs= {
                                        'service_description': "WEB_PUBLIC_"+name,
                                        data.service_key_hostname: data.hostname,
                                        'use': "ST_WEB"+web.use_type,
                                        'check_command': web.command+"!"
                                                         +web.hostname+"!"
                                                         +web.url+"!"
                                                         +web.warning|string+"!"
                                                         +web.critical|string+"!"
                                                         +web.timeout|string+"!"
                                                         +web.strings+"!"
                                                         +web.other_args,
                                    })
        }}
    {% endfor %}
{% endif %}

{% endmacro %}
