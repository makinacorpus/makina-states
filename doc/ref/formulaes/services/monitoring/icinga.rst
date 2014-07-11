Icinga configuration
====================

See :ref:`module_mc_icinga` for configuration options.

About packaging
---------------

The icinga module can provide:

  - configuration of icinga core
  - configuration of database for ido2db
  - configuration of ido2db daemon
  - configuration of uwsgi in order to serve cgi
  - configuration of nginx to serve cgi through uwsgi


The icinga_web module can provide:

  - configuration of icinga web
  - configuration of database for icinga web
  - configuration of php-fpm
  - configuration of nginx to serve php webpages through php-fpm

icinga_web module can configure its nginx virtualhost to serve cgi but icinga_web module doesn't configure uwsgi and doesn't install any file related to cgi.

The reason is to keep icinga and icinga_web independants.
icinga-web and icinga can be installed on two differents hosts but CGI files require to have icinga-core installed on the host.

icinga_web module depends on icinga module only if cgi is enabled in icinga-web virtualhost (makina-states.services.monitoring.icinga_web.nginx.icinga_cgi.enabled is set to True).

In the same way, icinga_web doesn't depends on pnp4nagios even if the module is enabled.
You have to install pnp4nagios separately.

The mysql configuration doesn't work.


The architecture of service folder looks like to :

    :init.sls: is the file which includes the others
    :hooks.sls: defines some states for schedule
    :macros.jinja: is empty because I don't have used macros for icinga and icinga_web
    :prerequisites.sls: defines states which install packages
    :configuration.sls: defines states which write configuration and init scripts
    :services.sls: defines states which start the service
    :pgsql.sls: the states which install and configure postgresql if this dependance is needed. The states are called before ones in prerequisites.sls
    :mysql.sls: the states which install and configure mysql if this dependance is needed. The states are called before ones in prerequisites.sls
    :nginx.sls: the states which install and configure nginx and phpfpm if theses dependances are needed. The states are called before ones in prerequisites.sls

For "pgsql.sls", "mysql.sls" and "nginx.sls", I don't have separated the states between prerequisites, configuration and services.


The architecture between Icinga, Icinga-web and nagvis looks like to:

::

	Icinga --ido2db--> Postgresql <---- Icinga-web
	     |
	     +---mklivestatus--><---------- Nagvis
             |
             +---npcdmod--><-npcd-><------- Pnp4nagios


Please note that icinga service offers two special macros to generate configurations.

Macros
------

configuration_add_object
++++++++++++++++++++++++

This macro was written in order to add an object in the icinga configuration

::

    {% import "makina-states/services/monitoring/icinga/init.sls" as icinga with context %}
    {{ icinga.configuration_add_object(type, file, attrs, **kwargs) }}

with

    :type: the type of added object
    :file: the filename of the added object
    :attrs: a dictionary in which each key corresponds to a directive

The default directory where configuration files are located is::

    /etc/icinga/objects/salt_generated/

**Before generating the configuration, all files and directories located in the directory are unlinked**. It is to avoid to detect
what are the objects which must be deleted.

You can change the configuration directory using \*\*kwargs parameter


A call with::

    {{ icinga.configuration_add_object(
                                   type='host',
                                   file='hosts/hostname1.cfg',
                                   attrs={
                                            'host_name': "hostname1",
                                            'use': "generic-host",
                                        },
                                  ) }}

Generates the file in /etc/icinga/objects/salt_generated/host/hostname1.cfg containing::

    define host {
     use=generic-host
     host_name=hostname1
    }


The services are managed in the same way::

    {{ icinga.configuration_add_object(
                                   type='service',
                                   file='services/SSH',
                                   attrs={
                                            'use': "generic-service",
                                            'service_description': "SSH",
                                        },
                                  ) }}

That generates the file /etc/icinga/objects/salt_generated/service/SSH.cfg containing::

    define service {
     use=generic-service
     service_description=SSH
    }


configuration_edit_object
+++++++++++++++++++++++++

This macro was written because some values in object configuration depends on the rest of the configuration.

For example, you can have::

    host_name=host1,host2,host3

in a service definition

But when you call the configuration_add_object, you don't know what hosts will be listed in this directive.


::

    {% import "makina-states/services/monitoring/icinga/init.sls" as icinga with context %}
    {{ icinga.configuration_edit_object(type, file, attr, value, **kwargs) }}

with

    :type: the type of edited object
    :file: the name of the edited object
    :attr: the directive for which a value must be added
    :value: the value added

The old values of the attr directive are not removed. 

If you call::

    {{ icinga.configuration_edit_object(type='service',
                                        file='SSH.cfg',
                                        attr='host_name',
                                        value='hostname1') }}

the previous service definition becomes::

    define service {
     use=generic-service
     service_description=SSH
     host_name=hostname1
    }

If you recall the macro with a different value::

    {{ icinga.configuration_edit_object(type='service',
                                        file='SSH.cfg',
                                        attr='host_name',
                                        value='hostname2') }}

the previous service definition becomes::

    define service {
     use=generic-service
     service_description=SSH
     host_name=hostname1,hostname2
    }


Limits
++++++

Currently, the macro doesn't edit the icinga.cfg file in order to add the directory in the list of "cfg_dir"
You should think to make a coherent configuration.

By default, the /etc/icinga/objects is present in "cfg_dir".

No checks are done. You can add invalid values for any directives. You can set non-existent directives too.


With the old macro, it was possible to recall the macro to add an object already added and all the parameters were merged.
Now it is not possible. You can add an object only one time but you can complete it with the second macro.

In comparaison to the previous version:
It is not possible to define several objects in one call. It is not possible to know if an attribute can accept several values or not.

configuration_add_auto_host
+++++++++++++++++++++++++++

This macro is designed to add an host and associated services

::

    {% import "makina-states/services/monitoring/icinga/init.sls" as icinga with context %}
    {% icinga.configuration_add_auto_host(hostname,
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

with

    :hostname: the hostname of the added host
    :hostgroup: if true, a hostgroup will be added instead of a simple host (because it is possible to add services for a hostgroup)
    :attrs: a dictionary in which each key corresponds to a directive in the host definition
    :ssh_user: user to connect the host (it is used by check_by_ssh command)
    :ssh_addr: address used to do the ssh connection in order to perform check_by_ssh. this address is not the hostname address becasue we can use a ssh gateway
    :ssh_port: ssh_port
    :[service]: a boolean to indicate that the service [service] has to be added
    :services_attrs: a dictionary to override the default values for each service definition and to ad additional values. The keys begining with "cmdarg_" are the check command arguments. Each subdictionary corresponds to a service.

Some services use an additional subdictionary because they can be defined several times. It is the case of

  - dns_association
  - dns_reverse_assocation
  - disk_space
  - network
  - solr
  - web_openid
  - web

For theses services, you may complete the services_attrs dictionary by adding a subdictionary ('a_service' here)::
    service_attrs: {
        'dns_association': {
            'a_service': {
                'cmdarg_hostname': "www.example.net",
            }
        }
    }

You can add several dns_association, disk_space, network, ...

For others services, the directives are not in a subdctionary::
    service_attrs: {
        'raid': {
            'check_command': "check",
        }
    }


You have to insert in services_attrs only the non default values.

Note: The directive "host_name" will not be taken into account. The value will be replace by the value of "hostname" argument

The host is added in /etc/icinga/objects/salt_generated/<hostname>/host.cfg
The services are added in this directory too (for ssh it will be /etc/icinga/objects/salt_generated/<hostname>/ssh.cfg)

The services are defined specially for the host.
There is no::

    define service {
        host_name host1,host2
    }

The commands definitions are located in objects/objects_defintions subdictionary in mc_icinga.py
They are installed with a state in configuration.sls.

All the commands objects are created even if no service use them.

