Nagvis configuration
====================

See :ref:`module_mc_nagvis` for configuration options.

Please note that we offer two special macros to generate configurations.

One macro is designed to add a map and the other is to add a geomap

add_map macro
-------------

::

{% import "makina-states/services/monitoring/nagvis/init.sls" as nagvis with context %}
{{ uwsgi.add_map(name, _global, objects, **kwargs) }}

with

    :name: name of the map (it is the filename too, so each name must be unique)
    :_global: dictionary in wich contians directives for 'define global{}' section
    :object: dictionary wich defines all objects

The object dictionary looks like:

::

	'objects': {
	    'abc': {
	        'type': "host",
	        'host_name': "host1",
	        'x': 4,
	        'y': 3,
	    },
	    'def': {
	        'type': "service",
	        'host_name': "host1",
	        'service_description': "SSH",
	        'x': 4,
	        'y': 3,
             },
         },

The keys are the values for "object_id" directives and "type" corresponds to the type of objects. 
The values for key "type" can be "host", "service", "servicegroup", "hostgroup", ...

You can add directives as key:value in each subdictionary

The macro produce a cfg files in /etc/nagvis/maps/name.cfg

add_geomap macro
----------------
::

{% import "makina-states/services/monitoring/nagvis/init.sls" as nagvis with context %}
{{ uwsgi.add_geomap(name, hosts, **kwargs) }}

with

    :name: name of the geomap (it is the filename too, so each name must be unique)
    :hosts: dictionary in which each subdictionary defines a host

The hosts dictionary looks like:

::

	'hosts': {
	    'ham-srv1': {
	        'description': "Hamburg Server 1",
	        'lat': 53.556866,
	        'lon': 9.994622,
	    },
	    'mun-srv1': {
	        'description': "Munich Server 1",
	        'lat': 48.1448353,
	        'lon': 11.5580067,
	    },
	},

The macro produce a svg files like

::

	muc-srv1;Munich Server 1;48.1448353;11.5580067
	ham-srv1;Hamburg Server 1;53.556866;9.994622

