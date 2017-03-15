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
  - configuration of icinga (add/remove objects configuration)


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

	icinga---ido2db---------><-postgresql-><---icinga-web
	     |
	     +---mklivestatus---><-----------------nagvis
             |
             +---npcdmod--------><-npcd-><-rrd-><--pnp4nagios


Please note that icinga service offers four special macros to generate configurations. Theses macros are described below.

Configuration
-------------

In configuration.sls, the general configuration of icinga and the objects configuration are made
For the objects configuration, some macros are called automatically with the content defined in::

    makina-states.services.monitoring.icinga.objects

This dictionary architecture looks like:

    :directory: directory in which configurations files will be written (default: /etc/icinga/objects/salt_generated)
    :objects_definition: dictionary in which each subdictionary is given to "configuration_add_object" macro as \*\*kwargs. It is used to define objects like contacts or timeperiods or commands
    :autoconfigured_hosts_definitions: dictionary in which each subdictionary is given to "configuration_add_auto_host" macro as \*\*kwargs. It is used to define hosts and hostgroups and add services associated to them.
    :purge_definitions: a list of files or directory which can be deleted. Each element of the list is given to "configuration_remove_object" macro as \*\*kwargs)

The "purge\_definitions" list is used to remove hosts. because a call to "configuration_add_auto_host" macro with all services disabled will remove only the services and not the host itself.

Macros
------

configuration_add_object
++++++++++++++++++++++++

This macro was written in order to add an object in the icinga configuration

::

    {% import "makina-states/services/monitoring/icinga/init.sls" as icinga with context %}
    {{ icinga.configuration_add_object(type, file, attrs, definition, **kwargs) }}

with

    :type: the type of added object
    :file: the filename of the added object
    :attrs: a dictionary in which each key corresponds to a directive
    :definition: the name used to identify the definition. It is the name used by configuration_edit_object. If none, configuration_edit_object will not work for this definition

The default directory where configuration files are located is::

    /etc/icinga/objects/salt_generated/

The directory can be modified in the "makina-states.services.monitoring.icinga.objects" dictionary


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

configuration_remove_object
+++++++++++++++++++++++++++

This macro was written in order to remove an object in the icinga configuration

::

    {% import "makina-states/services/monitoring/icinga/init.sls" as icinga with context %}
    {{ icinga.configuration_remove_object(file, **kwargs) }}

with

    :file: the filename of the added object

The default directory where configuration files are located is::

    /etc/icinga/objects/salt_generated/

The directory can be modified in the "makina-states.services.monitoring.icinga.objects" dictionary

configuration_edit_object
+++++++++++++++++++++++++

This macro was written because some values in object configuration depends on the rest of the configuration.

For example, you can have::

    host_name=host1,host2,host3

in a service definition

But when you call the configuration_add_object, you don't know what hosts will be listed in this directive.


::

    {% import "makina-states/services/monitoring/icinga/init.sls" as icinga with context %}
    {{ icinga.configuration_edit_object(type, file, attr, value, auto_host, definition, **kwargs) }}

with

    :type: the type of edited object
    :file: the name of the edited object
    :attr: the directive for which a value must be added
    :value: the value added
    :auto_host: true if the file is a file created with configuration_add_auto_host macro
    :definition: the definition to edit in the file

The "file" argument value is relative to "makina-states.services.monitoring.icinga.objects.directory" (default: /etc/icinga/objects/salt_generated/)

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

when auto_host is set to true, the value for definition argument are:

  - definition='host': or definition='hostgroup' the attribute will be added in the host/hostgroup definition 
  - definition=service: the attribute will be added in service definition. service have to be in the service list and have to be enabled
  - definition=service-name: the attribute will be added in service loop definition.


Limits
++++++

Currently, the macro doesn't edit the icinga.cfg file in order to add the directory in the list of "cfg_dir"
You should think to make a coherent configuration.

By default, the /etc/icinga/objects is present in "cfg_dir".

No checks are done. You can generate invalid values for any directives. You can set non-existent directives too.

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
    :services_attrs: a dictionary to override the default values for each service definition and to ad additional values. The keys begining with "cmdarg\_" are the check command arguments. Each subdictionary corresponds to a service.

Some services use an additional subdictionary because they can be defined several times. It is the case of

  - dns_association
  - dns_reverse_assocation
  - disk_space
  - network
  - solr
  - web_openid
  - web


For theses services, you may complete the services_attrs dictionary by adding a subsubdictionary
(the dictionary associatio to 'a_service' key here)::

    service_attrs: {
        'dns_association': {
            'a_service': {
                'cmdarg_hostname': "www.example.net",
            }
        }
    }

You can add several dns_association, disk_space, network, solr, web_openid, web

For others services, the directives are not in a subsubdctionary but directly in the subdictionary::

    service_attrs: {
        'raid': {
            'check_command': "check",
        }
    }


You have to insert in services_attrs only the non default values.


Note: The directive "host_name" will not be taken into account.
The value will be replaced with the value of "hostname" macro argument

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

All the complexity is in "mc_icinga.add_auto_configuration_host_settings" function (see :ref:`module_mc_icinga`)

The macro only adds the host (or hostgroup) by calling "configuration_add_object" and browses the services.

if the service is enabled:
  a state adds the service configuration file by calling the "configuration_add_object" macro
if the service is disabled:
  a state removes the service configuration file by calling the "configuration_remove_object" macro

For each host, a state is executed for each service even if all the services are disabled.
The execution takes about 30 minutes for 128 hosts and 50 services (the macro configuration_add_object is called 939 times and configuration_remove_object is called 6158 times
(yes, it doesn't correspond to 50*128 because there are the commands definitions, contacts, ...)).

The speed can be improved by removing the "watch\_in" directive in the "configuration_remove_object" macro (because this macro is called a lot of time).

Without this directive. the execution takes about 10 minutes for 128 hosts and 50 services but the configuration files are removed after the restart of icinga.

I don't have find how to fix this problem. I used a "order: 1" directive but in this case the states are executed before prerequisite (which is less problematic than when the execution was after the restart of icinga. The files are deleted before the creation of new files. If a file is in "purge\_definitions" dictionary and is created in another macro call. The file will be deleted and recreated in a next state)

Another idea is to delete several configuration files with only one state.


Off topic:
I have used "order" directive in configuration_add_object macro too. (the execution time seems to be the same without any directive like order or watch_in and with a order directive)

The execution is 629.685 secondes for 128 hosts, 50 services and "order" instead of "watch\_in" in "configuration_add_object" and "configuration_remove_object"

Without the "order" directive in configuration_add_object macro but with a "watch\_in" directive, the execution is 820.238 secondes.

The difference is 190.553 for 939 "watch\_in" (the 939 call of "configuration\_add\_object" macro). So a \"watch\_in\" directive take 0.203 secondes

With 6158 "watch\_in" for "configuration\_remove\_object", it is (0.203*6158) 1249.654 secondes (about 20 minutes).

I have supposed "watch\_in" execution time constant.

With 50 services per hosts (ignore services_loop which can increase the number of services): The host autoconfiguration macro need about 10.353 secondes to execute "watch\_in" directives in one call.

With about 360 hosts the excessive execution time approach the entire hour.

The issue was resolved by decreasing the number of states: there is only one state to create each host.
The services for the host are in the same file.

This decrease the number of states and the call to configuration_remove_object is useless to delete old services because the file with services of the hosts
is naturally edited.

The execution time decrease to 1 minute about for 128 hosts but with 1000 hosts it ran out of memory.
However, it is perhaps a bad idea to have all services in a same file because the files becomes long.

The memory problem was solved by moving the "object" subdiction so that it is not cached.
Only a list of hosts is cached is "object" subdictionary.

The function "get_settings_for_object" is designed to get non cached values.

An other modification is that the macro doesn't give the data to template.
Before the modification it was::

    {% set data = salt['mc_icinga.add_auto_configuration_host_settings'](...) %}
    icinga-configuration-{{data.state_name_salt}}-add-auto-host-conf:
        ...
        - defaults
          data: |
                {{sdata}}

Now, the data are stored in a light dictionary in global variables in "mc_icinga.add_auto_configuration_host.objects"
In the macro there is::

    {% set data = salt['mc_icinga.add_auto_configuration_host'](...) %}
    icinga-configuration-{{data.state_name_salt}}-add-auto-host-conf:
        ...
        - defaults
          hostname: |
                {{salt['mc_utils.json_dump'](data.hostname}}

The function "mc_icinga.add_auto_configuration_host" stores the object informations in a dictionary like::

    {
        'hostname': {}
    }

Each subdictionary contains all arguments given to the macro.
But this methods requires to store a lot of data. For objects which are in localsettings, I have added a "fromsetting" argument. Instead of store all arguments given to the macro, only the key in localsettings is stored::

    {
        'hostname': {'fromsettings': 'host1'}
    }

Only key of this dictionary is given to template. 
The template get the object from localsettings by calling "get_settings_for_object" if a "fromsettings" key is found.
And the settings are given to the previous "mc_icinga.add_auto_configuration_host_settings" function.

All is done in the template in order to avoid store a lot of data in memory during a long time.
Then, a lot of memory is used during template compilation, when::

    default:
      data: |
            {{sdata}}

is replaced with::

    default:
      data: |
            {a big dictionary here which is the return of utf8 encode in order to use more memory}



With theses modifications, it is possible to manage only 7000 hosts with 10 services per host with 1Go of memory (another 800Mo of memory is needed to run salt-master).


Add a new service in configuration_add_auto_host macro
++++++++++++++++++++++++++++++++++++++++++++++++++++++

If you want add a new service managed with this macro, you have to:

  1. add arguments in macro and in add_auto_configuration_host_settings function
  2. add the service in "services" or "services_loop" list
  3. add the default values in "services_default_attrs"
  4. if the service was added in "services_loop" list, add code to merge dictionaries
  5. if the default "check_command" is new, add a "command" definition in
     "objects_definitions" dictionary (in "objects" function)
     and add the command with its arguments in "check_command_args"




