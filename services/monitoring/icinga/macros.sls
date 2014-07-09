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
#     services_attrs
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
                                     dns_association_hostname=False,
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
                                     services_attrs={}
                                    ) %}
{% set data = salt['mc_icinga.add_auto_configuration_host_settings'](hostname,
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
                                                                     dns_association_hostname,
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
                                                                     services_attrs,
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
                                attrs=data.services_attrs.backup_burp_age 
                               )
    }}
{% endif %}

# add backup_rdiff service
# TODO/ok: edit command in order to allow customization in check_by_ssh
{% if data.backup_rdiff %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/backup_rdiff.cfg',
                                attrs=data.services_attrs.backup_rdiff
                               )
    }}
{% endif %}

# add beam_process service
{% if data.beam_process %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/beam_process.cfg',
                                attrs=data.services_attrs.beam_process
                               )
    }}
{% endif %}

# add celeryd_process service
{% if data.celeryd_process %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/celeryd_process.cfg',
                                attrs=data.services_attrs.celeryd_process
                               )
    }}
{% endif %}

# add cron service
# TODO/ok: edit command in order to allow customization in check_by_ssh
{% if data.cron %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/cron.cfg',
                                attrs=data.services_attrs.cron
                               )
    }}
{% endif %}

# add ddos service
# TODO/ok: edit command in order to allow customization in check_by_ssh
{% if data.ddos %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/ddos.cfg',
                                attrs=data.services_attrs.ddos
                               )
    }}
{% endif %}

# add debian_updates service
# TODO/ok: edit command in order to allow customization in check_by_ssh
{% if data.debian_updates %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/debian_updates.cfg',
                                attrs=data.services_attrs.debian_updates
                               )
    }}
{% endif %}

# add dns_association_hostname service
{% if data.dns_association_hostname %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/dns_association_hostname.cfg',
                                attrs=data.services_attrs.dns_association_hostname
                               )
    }}
{% endif %}

# add dns_association service 
{% if data.dns_association %}
    {% for name, dns_association in data.services_attrs.dns_association.items() %}
        {{ configuration_add_object(type='service',
                                    file=data.service_subdirectory+'/'+data.hostname+'/dns_association_'+name+'.cfg',
                                    attrs=dns_association
                                   )
        }}
    {% endfor %}
{% endif %}

# add dns_reverse_association service
{% if data.dns_reverse_association %}
    {% for name, dns_reverse_association in data.services_attrs.dns_reverse_association.items() %}
        {{ configuration_add_object(type='service',
                                    file=data.service_subdirectory+'/'+data.hostname+'/dns_reverse_association_'+name+'.cfg',
                                    attrs=dns_reverse_association
                                   )
        }}
    {% endfor %}
{% endif %}

# add disk_space service
{% if data.disk_space %}
    {% for mountpoint, disk_space in data.services_attrs.disk_space.items() %}
        {{ configuration_add_object(type='service',
                                    file=data.service_subdirectory+'/'+data.hostname+'/disk_space_'+mountpoint+'.cfg',
                                    attrs=disk_space
                                   )
        }}
    {% endfor %}
{% endif %}

# add drbd service
# TODO/ok: edit command in order to allow customization in check_by_ssh
# TODO: add contact groups
{% if data.drbd %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/drbd.cfg',
                                attrs=data.services_attrs.drbd
                               )
    }}
{% endif %}

# add epmd_process service
{% if data.epmd_process %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/epmd_process.cfg',
                                attrs=data.services_attrs.epmd_process
                               )
    }}
{% endif %}

# add erp_files service
# TODO/ok: edit command in order to allow customization in check_by_ssh
# TODO: add contact groups
{% if data.erp_files %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/erp_files.cfg',
                                attrs=data.services_attrs.erp_files
                               )
    }}
{% endif %}

# add fail2ban service
{% if data.fail2ban %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/fail2ban.cfg',
                                attrs=data.services_attrs.fail2ban
                               )
    }}
{% endif %}

# add gunicorn_process service
{% if data.gunicorn_process %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/gunicorn_process.cfg',
                                attrs=data.services_attrs.gunicorn_process
                               )
    }}
{% endif %}

# add haproxy service
{% if data.haproxy %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/haproxy.cfg',
                                attrs=data.services_attrs.haproxy
                               )
    }}
{% endif %}

# add ircbot_process service
{% if data.ircbot_process %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/ircbot_process.cfg',
                                attrs=data.services_attrs.ircbot_process
                               )
    }}
{% endif %}

# add load avg service
{% if data.load_avg %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/load_avg.cfg',
                                attrs=data.services_attrs.load_avg
                               )
    }}
{% endif %}

# add mail_cyrus_imap_connections service
# TODO/ok: edit command in order to allow customization in check_by_ssh
{% if data.mail_cyrus_imap_connections %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/mail_cyrus_imap_connections.cfg',
                                attrs=data.services_attrs.mail_cyrus_imap_connections
                               )
    }}
{% endif %}

# add mail_imap service
{% if data.mail_imap %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/mail_imap.cfg',
                                attrs=data.services_attrs.mail_imap
                               )
    }}
{% endif %}

# add mail_imap_ssl service
{% if data.mail_imap_ssl %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/mail_imap_ssl.cfg',
                                attrs=data.services_attrs.mail_imap_ssl
                               )
    }}
{% endif %}

# add mail_pop service
{% if data.mail_pop %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/mail_pop.cfg',
                                attrs=data.services_attrs.mail_pop
                               )
    }}
{% endif %}

# add mail_pop_ssl service
{% if data.mail_pop_ssl %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/mail_pop_ssl.cfg',
                                attrs=data.services_attrs.mail_pop_ssl
                               )
    }}
{% endif %}

# add mail_pop_test_account service
{% if data.mail_pop_test_account %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/mail_pop_test_account.cfg',
                                attrs=data.services_attrs.mail_pop_test_account
                               )
    }}
{% endif %}

# add mail_server_queues service
# TODO/ok: edit command in order to allow customization in check_by_ssh
{% if data.mail_server_queues %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/mail_server_queues.cfg',
                                attrs=data.services_attrs.mail_server_queues
                               )
    }}
{% endif %}

# add mail_smtp service
{% if data.mail_smtp %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/mail_smtp.cfg',
                                attrs=data.services_attrs.mail_smtp
                               )
    }}
{% endif %}

# add md_raid service
# TODO/ok: edit command in order to allow customization in check_by_ssh
{% if data.md_raid %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/md_raid.cfg',
                                attrs=data.services_attrs.md_raid
                               )
    }}
{% endif %}

# add megaraid_sas service
{% if data.megaraid_sas %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/megaraid_sas.cfg',
                                attrs=data.services_attrs.megaraid_sas
                               )
    }}
{% endif %}

# add memory service
{% if data.memory %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/memory.cfg',
                                attrs=data.services_attrs.memory
                               )
    }}
{% endif %}

# add memory_hyperviseur service
{% if data.memory_hyperviseur %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/memory_hyperviseur.cfg',
                                attrs=data.services_attrs.memory_hyperviseur
                               )
    }}
{% endif %}

# add mysql_process service
{% if data.mysql_process %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/mysql_process.cfg',
                                attrs=data.services_attrs.mysql_process
                               )
    }}
{% endif %}

# add network service
{% if data.network %}
    {% for name, network in data.services_attrs.network.items() %}
        {{ configuration_add_object(type='service',
                                    file=data.service_subdirectory+'/'+data.hostname+'/network_'+name+'.cfg',
                                    attrs=network
                                   )
        }}
    {% endfor %}
{% endif %}

# add ntp_peers service
# TODO/ok: cssh
{% if data.ntp_peers %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/ntp_peers.cfg',
                                attrs=data.services_attrs.ntp_peers
                               )
    }}
{% endif %}

# add ntp_time service
# TODO/ok: cssh
{% if data.ntp_time %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/ntp_time.cfg',
                                attrs=data.services_attrs.ntp_time
                               )
    }}
{% endif %}

# add only_one_nagios_running service
{% if data.only_one_nagios_running %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/only_one_nagios_running.cfg',
                                attrs=data.services_attrs.only_one_nagios_running
                               )
    }}
{% endif %}

# add postgres_port service
{% if data.postgres_port %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/postgres_port.cfg',
                                attrs=data.services_attrs.postgres_port
                               )
    }}
{% endif %}

# add postgres_process service
{% if data.postgres_process %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/postgres_process.cfg',
                                attrs=data.services_attrs.postgres_process
                               )
    }}
{% endif %}

# add prebill_sending service
# TODO/ok: edit command in order to allow customization in check_by_ssh
{% if data.prebill_sending %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/prebill_sending.cfg',
                                attrs=data.services_attrs.prebill_sending
                               )
    }}
{% endif %}

# add raid service
# TODO/ok: edit command in order to allow customization in check_by_ssh
{% if data.raid %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/raid.cfg',
                                attrs=data.services_attrs.raid
                               )
    }}
{% endif %}

# add sas service
# TODO/ok: edit command in order to allow customization in check_by_ssh
{% if data.sas %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/sas.cfg',
                                attrs=data.services_attrs.sas
                               )
    }}
{% endif %}

# add snmpd_memory_control service
{% if data.snmpd_memory_control %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/snmpd_memory_control.cfg',
                                attrs=data.services_attrs.snmpd_memory_control
                               )
    }}
{% endif %}

# add solr service
# TODO: readd auth
{% if data.solr %}
    {% for name, solr in data.services_attrs.solr.items() %}
        {{ configuration_add_object(type='service',
                                    file=data.service_subdirectory+'/'+data.hostname+'/solr_'+name+'.cfg',
                                    attrs=solr
                                   )
        }}
    {% endfor %}
{% endif %}

# add ssh service
{% if data.ssh %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/ssh.cfg',
                                attrs=data.services_attrs.ssh
                               )
    }}
{% endif %}

# add supervisord_status service
# TODO/ok: edit command in order to allow customization in check_by_ssh
{% if data.supervisord_status %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/supervisord_status.cfg',
                                attrs=data.services_attrs.supervisord_status
                               )
    }}
{% endif %}

# add swap service
# TODO/ok: edit command in order to allow customization in check_by_ssh
{% if data.swap %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/swap.cfg',
                                attrs=data.services_attrs.swap
                               )
    }}
{% endif %}

# add tiles_generator_access service
{% if data.tiles_generator_access %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/tiles_generator_access.cfg',
                                attrs=data.services_attrs.tiles_generator_access
                               )
    }}
{% endif %}

# add 3ware raid  service (check by ssh)
{% if data.ware_raid %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/3ware_raid.cfg',
                                attrs=data.services_attrs.ware_raid
                               )
    }}
{% endif %}

# add web apache status service
{% if data.web_apache_status %}
    {{ configuration_add_object(type='service',
                                file=data.service_subdirectory+'/'+data.hostname+'/web_apache_status.cfg',
                                attrs=data.services_attrs.web_apache_status
                               )
    }}
{% endif %}

# add web_openid service
# TODO: readd auth
{% if data.web_openid %}
    {% for name, web_openid in data.services_attrs.web_openid.items() %}
        {{ configuration_add_object(type='service',
                                    file=data.service_subdirectory+'/'+data.hostname+'/web_openid_'+name+'.cfg',
                                    attrs=web_openid
                                   )
        }}
    {% endfor %}
{% endif %}

# add web service
# TODO/ok: readd auth
{% if data.web %}
    {% for name, web in data.services_attrs.web.items() %}
        {{ configuration_add_object(type='service',
                                    file=data.service_subdirectory+'/'+data.hostname+'/web_'+name+'.cfg',
                                    attrs=web
                                   )
        }}
    {% endfor %}
{% endif %}


{% endmacro %}
