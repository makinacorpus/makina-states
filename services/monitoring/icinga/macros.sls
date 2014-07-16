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

# add the object
icinga-configuration-{{data.state_name_salt}}-add-object-conf:
  file.managed:
    - name: {{data.objects.directory}}/{{data.file}}
    - source: salt://makina-states/files/etc/icinga/objects/template.cfg
    - user: root
    - group: root
    - mode: 644
    - makedirs: True
    - order: 1
    {#
    - watch:
      - mc_proxy: icinga-configuration-pre-object-conf 
    - watch_in:
      - mc_proxy: icinga-configuration-post-object-conf
    #}
    - template: jinja
    - defaults:
      data: |
            {{sdata}}
{% endmacro %}

{#
#
# Macros mains args:
#     file
#         the filename where the object will be removed
#
#     the macro doesn't delete the file. The file is added into a list and the state
#     icinga-configuration-remove-objects-conf (configuration.sls) removes the files
#     in the list
#
#}

{% macro configuration_remove_object(file) %}

# add the file in the list of objects to remove
{% set res = salt['mc_icinga.remove_configuration_object'](file) %}

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

# split the value in ',' and loop. it is to remove duplicates values.
# for example, it is to avoid to produce "v1,v2,v1" if "v1,v2" are given in a call and "v1" in an other call
{% for value_splitted in data.value.split(',') %}
icinga-configuration-{{data.state_name_salt}}-attribute-{{data.attr}}-{{value_splitted}}-edit-object-conf:
  file.accumulated:
    - name: "{{data.attr}}"
    - filename: {{data.objects.directory}}/{{data.file}}
    - text: "{{value_splitted}}"
    - watch:
      - mc_proxy: icinga-configuration-pre-accumulated-attributes-conf
    - watch_in:
      - mc_proxy: icinga-configuration-post-accumulated-attributes-conf
      - file: icinga-configuration-{{data.type}}-{{data.name}}-add-object-conf
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
                                     services_attrs={}
                                    ) %}
{% set data = salt['mc_icinga.add_auto_configuration_host_settings'](hostname=hostname,
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
                                                                     **kwargs
                                                                    ) %}
{% set sdata = salt['mc_utils.json_dump'](data) %}

# add the host/hostgroup object
{{ configuration_add_object(type=data.type,
                            file='/'.join([data.service_subdirectory, data.hostname, data.type+'.cfg']),
                            attrs=data.attrs) }}


# configure the services
{% for service, enabled in data.services_enabled.items() %}
    {% set file='/'.join([data.service_subdirectory, data.hostname, service+'.cfg']) %}
    {% if enabled %}
        {{ configuration_add_object(type='service',
                                    file=file,
                                    attrs=data.services_attrs[service]
                                   )
        }}
    {% else %}
        {{ configuration_remove_object(file=file) }}
    {% endif %}
{% endfor %}


# configure the loop services
# TODO: it removes only services which are in services_attrs subdictionaries if the subdictionaries are removed, service deletion will not work
# unless the service is kept in the subdictionary and the service argument is set to False. the configuration_remove_object macro can be used too
{% for service, enabled in data.services_loop_enabled.items() %}
    {% for name, values in data.services_attrs[service].items() %}
        {% set file='/'.join([data.service_subdirectory, data.hostname, service, name+'.cfg']) %}
        {% if enabled %}
            {{ configuration_add_object(type='service',
                                        file=file,
                                        attrs=values
                                       )
            }}
        {% else %}
            {{ configuration_remove_object(file=file) }}
        {% endif %}
    {% endfor %}
{% endfor %}


{% endmacro %}
