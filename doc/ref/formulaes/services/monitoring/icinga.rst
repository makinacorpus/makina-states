Icinga configuration
====================

See :ref:`module_mc_icinga` for configuration options.

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


Please note that icinga service offers a special macros to generate configurations.

add_configuration
-----------------

::

    {% import "makina-states/services/monitoring/icinga/init.sls" as icinga with context %}
    {{ icinga.add_configuration(file, objects, keys_mapping, **kwargs) }}

with

    :file: the filename to create with the configuration. You can provide an absolute path. Otherwise the relative path are relative to "configuration_directory" directory ("/etc/icinga" by default)
    :objects: dictionary wich defines all objects.
    :keys_mapping: dictionary to etablish the associations between keys of dictionaries and directives


The objects dictionary looks like:

::

    'objects' = {
        'host': {
            'h1': {
                'alias': "host1",
                'use': "generic-host",
            },
        },
        'service': {
            'SSH': {
                'host_name': "h1",
            },
        },
        'hostdependency': [
            {
                'host_name': "h1"
            },
        ],
    }


The keys of each dictionaries are the value for directives defined in "keys_mapping" dictionary.

With the default keys_mapping::

    set keys_mapping_default = {
      'host': "host_name",
      'hostgroup': "hostgroup_name",
      'service': "service_description",
      'servicegroup': "servicegroup_name",
      'contact': "contact_name",
      'contactgroup': "contactgroup_name",
      'timeperiod': "timeperiod_name",
      'command': "command_name",
      'servicedependency': None,
      'serviceescalation': None,
      'hostdependency': None,
      'hostescalation': None,
      'hostextinfo': 'host_name',
      'serviceextinfo': 'host_name',
    }

the key "h1" is the value for host directive "host_name" and the key "SSH" is the value for directive "service_description".
When the value is set to None in the keys_mapping dictionary, the subdictionary become a list. It is usefull when no attribute has a unique value.

The generated configuration looks like to::

    define host {
        host_name=h1
        alias=host1
        use=generic-host
    }
    define service {
        service_description=SSH
        host_name=h1
    }
    define hostdependency {
        host_name=h1
    }

The macro allow to produce an invalid configuration with non-existent directives but forbide to have two same directives even if the values are different
(because of the use of a dictionary in which keys are unique)

If you have::

    'host': {
        'host1': {
            'host_name': "host2",
        }
    }

with::

    'host': "host_name",

in keys_mapping,

The produced file will contains::

    define host {
        host_name=host1
    }

The second value for "host_name" directive will be ignored
