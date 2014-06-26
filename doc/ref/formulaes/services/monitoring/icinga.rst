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


Please note that icinga service offers a special macros to generate configurations.

Macros
------

add_configuration
+++++++++++++++++

::

    {% import "makina-states/services/monitoring/icinga/init.sls" as icinga with context %}
    {{ icinga.add_configuration(directory, objects, keys_mapping, accumulated_values, **kwargs) }}

with

    :directory: the directory in which configuration must be written. You can provide an absolute path. Otherwise the relative path are relative to "configuration_directory" directory ("/etc/icinga" by default). The configuration will be located in subdirectories (one subdirectory per object types) with a file for each defined object. **Before generating the configuration, all files and directories located in the directory given are unlinked**.
    :objects: dictionary wich defines all objects. See below for structure.
    :keys_mapping: dictionary to establish the associations between keys of dictionaries and directives
    :accumulated_values: dictionary to establish the directives for which several values are allowed

**Before generating the configuration, all files and directories located in the directory given are unlinked**. It is to avoid to detect
what are the objects which must be deleted.


The objects dictionary looks like:

::

    'objects' = {
        'host': {
            'host1': {
                'alias': "foo",
                'use': "generic-host",
            },
        },
        'service': {
            'SSH': {
                'host_name': "h1",
            },
        },
        'hostdependency': {
            'dependency1' {
                'host_name': "host1"
            },
        },
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

the key "host1" is the value for host directive "host_name" in the host definition
and the key "SSH" is the value for directive "service_description".
When the value is set to None in the keys_mapping dictionary, the key is not used as a directive
but it is used for filename

The generated configuration looks like to::

    define host {
        host_name=host1
        alias=foo
        use=generic-host
    }
    define service {
        service_description=SSH
        host_name=host1
    }
    define hostdependency {
        host_name=host1
    }

Each object definition will be in its file:

  - the definition for host1 will be in `host/host1.cfg`
  - the defintion for ssh service will be in `service/SSH.cfg`
  - and the hostdependency will be in `hostdependency/dependency1.cfg`


The macro allow to produce an invalid configuration with non-existent directives but forbidde to have two same directives even if the values are different
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

You can call the macro several times. If you call a first time the macro with::

    'objects' = {
        'host': {
            'host1': {
                'parents': "host2"
                'alias': "foo",
            },
            'host2': {
            },
        },
    }


and a second time the macro with::

    'objects' = {
        'host': {
            'host1': {
                'parents': "host3"
                'alias': "bar",
                'use': "generic-host"
            },
        },
    }

the generated configuration will contain (if you use the default keys_mapping and accumulated_values)::

    define host {
        host_name=host1
        alias=foo
        parents=host1,host3
        use=generic-host
    }
    define host {
        host_name=host2
    }


The "parents" directive contains the two parents because "parents" is an accumulated value
but alias which is not one will contain only the first value given. The second value will be ignored.

The value for "use" is set because it was not given the first time.


Limits
++++++

The salt-stack states are naming with a hash of the object dictionary. If you call the macro several times with exactly the same
objects dictionary, errors will happen.


Currently, all the directives are stored in accumulators (it takes a lot of time).
The name used for accumulator looks like::

    "{{type}}-{{key_map}}-attribute-{{directive}}"

So, if you use this string in a directive name (not in the value), errors can hapen because the directives are
find from this string (the substring `{{type}}-{{key_map}}-attribute-` is removed)

Another problem is when you add::

    'attr': "v1,v2"

and in a second call, you add::

    'attr': "v2"

in this case, the second value "v2" is not removed and the generated file contains::

    attr=v1,v2,v2


Currently, the macro doesn't edit the icinga.cfg file in order to add the directory in the list of "cfg_dir"
You should think to make a coherent configuration.
