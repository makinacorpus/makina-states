Nagvis configuration
====================

See :ref:`module_mc_nagvis` for configuration options.

This service configure nagvis with a connection to icinga using mklivestatus
because nagvis currently can't connect to a postgresql database.

Nagvis doesn't depend on icinga unless mklivestatus socket is done with a unix pipe

Integration with icinga-web is done in icinga_web service.


Please note that we offer two special macros to generate configurations.

One macro is designed to add a map and the other is to add a geomap

add_map macro
-------------

::

{% import "makina-states/services/monitoring/nagvis/init.sls" as nagvis with context %}
{{ nagvis.add_map(name, _global, objects, keys_mapping, **kwargs) }}

with

    :name: name of the map (it is the filename too, so each name must be unique)
    :_global: dictionary in wich contians directives for 'define global{}' section
    :objects: dictionary wich defines all objects.
    :keys_mapping: dictionary to etablish the associations between keys of dictionaries and directives

The objects dictionary contains a subdictionary for each type of objects.
In each subdictionary, subsubdictionaries contains directives for each 'define <type> {}'

The keys of subsubdictionaries are the values of directives defined in the keys_mapping dictionary.
Because sometimes it is not possible to find a directive with unique value, if a value is set to "None", in the key_mapping dictionary,
the subdictionary become a list


The objects dictionary looks like:

::

    'objects' = {
        'host': {
            'h1': {
                'x': 4,
                'y': 3,

            },
        },
        'service': {
            'SSH': {
                'host_name': "h1",
                'x': 4,
                'y': 3,
             },
        },
    }


With the key_mapping dictionary:

::

    keys_mapping = {
        'host': "host_name",
        'hostgroup': "hostgroup_name",
        'service': "service_description",
        'servicegroup': "servicegroup_name",
        'map': "map_name",
        'textbox': None,
        'shape': None,
        'line': None,
        'template': None,
        'container': None,
    }

So, "h1" is the value for "host_name" directive and "SSH" is the value for "service_description" directive

You can add directives as key:value in each subdictionary

The macro produces a cfg file in /etc/nagvis/maps/name.cfg. This file contains

With the example above, the file located in /etc/nagvis/maps/name.cfg will contain:

::

    define global {
    }
    define host {
        host_name=h1
        x=4
        y=3
    }
    define service {
        host_name=h1
        service_description=SSH
        x=4
        y=3
    }
        


add_geomap macro
----------------
::

{% import "makina-states/services/monitoring/nagvis/init.sls" as nagvis with context %}
{{ nagvis.add_geomap(name, hosts, **kwargs) }}

with

    :name: name of the geomap (it is the filename too, so each name must be unique)
    :hosts: dictionary in which each subdictionary defines a host

The hosts dictionary looks like:

::

	'hosts': {
	    'ham-srv1': {
	        'alias': "Hamburg Server 1",
	        'lat': 53.556866,
	        'lon': 9.994622,
	    },
	    'mun-srv1': {
	        'alias': "Munich Server 1",
	        'lat': 48.1448353,
	        'lon': 11.5580067,
	    },
	},

The macro produces a csv file like

::

	muc-srv1;Munich Server 1;48.1448353;11.5580067
	ham-srv1;Hamburg Server 1;53.556866;9.994622

This macro produces only the /etc/nagvis/geomap/name.csv file and 
not the /etc/nagvis/maps/name.cfg file.
In order to produce the /etc/nagvis/maps/name.cfg file, you should call the "add_map" macro.


