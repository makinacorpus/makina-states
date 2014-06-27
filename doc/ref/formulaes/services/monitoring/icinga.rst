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

.. Call the macro automatically
.. ----------------------------
.. I have no idea.
.. Perhaps with a runner on the icinga host. but we must gvie it all configuration of all hosts
.. or
.. with a returner. The minions return to salt-master the state of services and salt-master generates a sls for icinga.
