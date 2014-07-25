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
#     definition
#         a string to identify the definition in the file. If none, configuration_edit_object macro will not be able
#         to edit this definition
#         the configuration_edit_object macro is removed for this time because the template for icinga2 are already complex 
#     fromsettings
#         instead of adding all object settings, only the name is stored and mc_icinga2.get_settings_for_object
#         will be called in the template to retrieve all the values
#         only the file argument is useful to set when fromsettings is used
#
#}

{% macro configuration_add_object(file, type=None, attrs={}, definition=None, fromsettings=None) %}
# add the object in the list of objects to add
{% set data = salt['mc_icinga2.add_configuration_object'](file=file,
                                                        type=type,
                                                        attrs=attrs,
                                                        definition=definition,
                                                        fromsettings=fromsettings,
                                                        get=False,
                                                        **kwargs) %}
{% endmacro %}

{#
#
# Macros mains args:
#     file
#         the filename where the object will be removed
#
#}

{% macro configuration_remove_object(file) %}
# add the file in the list of objects to remove
{% set data = salt['mc_icinga2.remove_configuration_object'](file=file, **kwargs) %}
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
#     ssh_user
#         user which is used to perform check_by_ssh
#     ssh_addr
#         address used to do the ssh connection in order to perform check_by_ssh
#         this address is not the hostname address because we can use a ssh gateway
#         if empty: take the value given for "hostname"
#     ssh_port
#         ssh port
#     services_attrs
#         dictionary to override the default values for each service definition and to add additional values.
#         the keys which name begins whit "cmdarg_" are the parameters for the check command
#     [service]
#         a boolean to indicate that the service [service] has to be checked (it generates the configuration file for the service)
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
                                     disk_space_tmp=False,
                                     disk_space_data=False,
                                     disk_space_mnt_data=False,
                                     disk_space_home=False,
                                     disk_space_var_lxc=False,
                                     disk_space_var_makina=False,
                                     disk_space_var_mysql=False,
                                     disk_space_var_www=False,
                                     disk_space_backups=False,
                                     disk_space_backups_guidtz=False,
                                     disk_space_var_backups_bluemind=False,
                                     disk_space_var_spool_cyrus=False,
                                     disk_space_nmd_www=False,
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
                                     services_attrs={},
                                     fromsettings=None
                                    ) %}
{% set data = salt['mc_icinga2.add_auto_configuration_host'](hostname=hostname,
                                                            hostgroup=hostgroup,
                                                            attrs=attrs,
                                                            ssh_user=ssh_user,
                                                            ssh_addr=ssh_addr,
                                                            ssh_port=ssh_port,
                                                            ssh_timeout=ssh_timeout,
                                                            backup_burp_age=backup_burp_age,
                                                            backup_rdiff=backup_rdiff,
                                                            beam_process=beam_process,
                                                            celeryd_process=celeryd_process,
                                                            cron=cron,
                                                            ddos=ddos,
                                                            debian_updates=debian_updates,
                                                            dns_association_hostname=dns_association_hostname,
                                                            dns_association=dns_association,
                                                            dns_reverse_association=dns_reverse_association,
                                                            disk_space=disk_space,
                                                            disk_space_root=disk_space_root,
                                                            disk_space_var=disk_space_var,
                                                            disk_space_srv=disk_space_srv,
                                                            disk_space_tmp=disk_space_tmp,
                                                            disk_space_data=disk_space_data,
                                                            disk_space_mnt_data=disk_space_mnt_data,
                                                            disk_space_home=disk_space_home,
                                                            disk_space_var_lxc=disk_space_var_lxc,
                                                            disk_space_var_makina=disk_space_var_makina,
                                                            disk_space_var_mysql=disk_space_var_mysql,
                                                            disk_space_var_www=disk_space_var_www,
                                                            disk_space_backups=disk_space_backups,
                                                            disk_space_backups_guidtz=disk_space_backups_guidtz,
                                                            disk_space_var_backups_bluemind=disk_space_var_backups_bluemind,
                                                            disk_space_var_spool_cyrus=disk_space_var_spool_cyrus,
                                                            disk_space_nmd_www=disk_space_nmd_www,
                                                            drbd=drbd,
                                                            epmd_process=epmd_process,
                                                            erp_files=erp_files,
                                                            fail2ban=fail2ban,
                                                            gunicorn_process=gunicorn_process,
                                                            haproxy=haproxy,
                                                            ircbot_process=ircbot_process,
                                                            load_avg=load_avg,
                                                            mail_cyrus_imap_connections=mail_cyrus_imap_connections,
                                                            mail_imap=mail_imap,
                                                            mail_imap_ssl=mail_imap_ssl,
                                                            mail_pop=mail_pop,
                                                            mail_pop_ssl=mail_pop_ssl,
                                                            mail_pop_test_account=mail_pop_test_account,
                                                            mail_server_queues=mail_server_queues,
                                                            mail_smtp=mail_smtp,
                                                            megaraid_sas=megaraid_sas,
                                                            memory=memory,
                                                            memory_hyperviseur=memory_hyperviseur,
                                                            mysql_process=mysql_process,
                                                            network=network,
                                                            ntp_peers=ntp_peers,
                                                            ntp_time=ntp_time,
                                                            only_one_nagios_running=only_one_nagios_running,
                                                            postgres_port=postgres_port,
                                                            postgres_process=postgres_process,
                                                            prebill_sending=prebill_sending,
                                                            raid=raid,
                                                            sas=sas,
                                                            snmpd_memory_control=snmpd_memory_control,
                                                            solr=solr,
                                                            ssh=ssh,
                                                            supervisord_status=supervisord_status,
                                                            swap=swap,
                                                            tiles_generator_access=tiles_generator_access,
                                                            ware_raid=ware_raid,
                                                            web_apache_status=web_apache_status,
                                                            web_openid=web_openid,
                                                            web=web,
                                                            services_attrs=services_attrs,
                                                            fromsettings=fromsettings,
                                                            get=False,
                                                            **kwargs
                                                                    ) %}

# add the host/hostgroup object and its services with only one state (the host and its services are in the same file)
# having all services associated to a host in one file avoid to delete files for disabled services
# the macro configuration_remove_object isn't called so much

# the main difference with the previous version, where there was one file per service is that the loops over services 
# are done in the template, not in the sls file.
icinga2-configuration-{{data.state_name_salt}}-add-auto-host-conf:
  file.managed:
    - name: {{data.objects.directory}}/{{data.file}}
    - source: salt://makina-states/files/etc/icinga2/conf.d/template_auto_configuration_host.conf
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
      hostname: |
                {{salt['mc_utils.json_dump'](hostname)}}


{% endmacro %}
