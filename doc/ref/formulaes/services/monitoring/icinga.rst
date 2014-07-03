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
    {{ icinga.configuration_add_object(type, name, attrs, **kwargs) }}

with

    :type: the type of added object
    :name: the name of the added object used for the filename
    :attrs: a dictionary in which each key corresponds to a directive

The default directory where configuration files are located is::

    /etc/icinga/objects/salt_generated/

**Before generating the configuration, all files and directories located in the directory are unlinked**. It is to avoid to detect
what are the objects which must be deleted.

You can change the configuration directory using \*\*kwargs parameter


A call with::

    {{ icinga.configuration_add_object(
                                   type='host',
                                   name='hostname1',
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
                                   name='SSH',
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
    {{ icinga.configuration_edit_object(type, name, attr, value, **kwargs) }}

with

    :type: the type of edited object
    :name: the name of the edited object
    :attr: the directive for which a value must be added
    :value: the value added

The old values of the attr directive are not removed. 

If you call::

    {{ icinga.configuration_edit_object(type='service',
                                        name='SSH',
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
                                        name='SSH',
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
                                         attrs={},
                                         ssh_user='root',
                                         ssh_addr,
                                         ssh_port=22,
                                         check_ssh=True,
                                         check_dns=True,
                                         check_dns_reverse=True,
                                         check_http=True,
                                         check_html=True,
                                         html={},
                                         check_ntp_peer=False,
                                         check_ntp_time=True,
                                         mountpoint_root=True,
                                         mountpoint_var=False,
                                         mountpoint_srv=False,
                                         mountpoint_data=False,
                                         mountpoint_home=False,
                                         mountpoint_var_makina=False,
                                         mountpoint_var_www=False,
                                         check_mountpoints=True,
                                         check_raid=False,
                                         check_md_raid=False,
                                         check_megaraid_sas=False,
                                         check_3ware_raid=False,
                                         check_cciss=False,
                                         check_drbd=False,
                                         check_swap=True,
                                         check_cpuload=True,
                                         check_procs=True,
                                         check_cron=True,
                                         check_debian_packages=False,
                                         check_burp_backup_age=False,
                                         check_rdiff=False,
                                         check_ddos=True,
                                         check_haproxy_stats=False,
                                         check_postfixqueue=False,
                                         check_postfix_mailqueue=True,
                                         services_check_command_args={}
                                        ) %}

with

    :hostname: the hostname of the added host
    :attrs: a dictionary in which each key corresponds to a directive in the host definition
    :ssh_user: user to connect the host (it is used by check_by_ssh command)
    :ssh_addr: address used to do the ssh connection in order to perform check_by_ssh. this address is not the hostname address becasue we can use a ssh gateway
    :ssh_port: ssh_port
    :check_*: boolean to indicate that the service has to be checked
    :services_check_command_args: dictionary to override the arguments given in check_command in each service
    :html: dictionary in wich subdictionaries define vhost, url and s a list of strings which must be found in the webpage (this dictionary is used only if check_html=True)


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

In commands, the icinga/nagios variables like '$HOSTADDRESS$' and '$HOSTNAME$' are not used in order to allow
overriding parameters with 'services_check_command_args' dictionary.

Only '$ARGN$' variables are used.

All parameters have not been added for each command because for most of them, no default value is given.
To add a new parameter:

  - Add the parameter in command definition located in objects_defintions dictionary
  - Add the default value in 'services_check_command_default_args' dictionary located in 'add_auto_configuration_host_settings'
    function (in mc_icinga.py)
  - Edit the 'attrs' dictionary in service defintion in macro configuration_add_auto_host




The syntax for 'html' argument is a dictionary for each url to check. In each dictionary, the url is defined and a list of strings.
Each string is looked for in the webpage.

The dictionary looks like::

    html = {
        'name1': {
            'hostname': "vhost1.localhost",
            'url': "/robots.txt",
            'auth': "",
            'expected_strings': ['Disallow'],
        },
    }

The key for subdictionaries ('name1' in the example) are used only for service filename.

The values in 'expected_strings' list are transformed in '-s "value1" -s "value2"' so that it can be used in only one argument for command
It may be possible to inject code.

It is possible to inject code with all icinga/nagios variables because it is not managed with bash, so that quotes arround variables are useless::

    command!" ; rm -r / ; echo "

is replace in::

    check_ssh -H "$ARG1$"

with::

    check_ssh -H "" ; rm -r / ; echo ""

the injection works.

I don't find any obvious solution to avoid injection in variables.

We can generate one command definition per service and hard code arguments with salt::

    define command {
        command_name check_ssh_for_hostname1
        command_line check_ssh -H 'hostname1'
    }

but it move the issue on salt. we can't know if a corrupted command will be generated.
