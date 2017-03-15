Registries
===========

Registries types
----------------
For each kind of configurations, we use salt execution modules as settings storages to store metadata, configuration settings and state inclusion registry. We have "global registries", inner subregistries and "sub inner registries" like "services", "services.settings" and "php.settings" registries.

Metadata registry & inclusion registries are only are mandatory for global sub registries.

Those registries are simple python dictionnaries.

The modules are many of the mc_states.mc_* modules (mc_services, mc_nodetypes, mc_php, etc)

Metadata
~~~~~~~~~
Registry which stock a name (eg: nodetypes, localsettings, services, controllers) and the global registries to load before this registry.

Example::

    {
        'name': 'controllers',
        'bases': ['localsettings'],
    }


Settings
~~~~~~~~~
Registry which stock arbitrary configuration settings related to the current registry.
Eg:

    - apache: registry.worker -> the mpm worker
    - localsettings: locations -> common path prefixes for various loations (/usr/bin, salt root)



Example::

    {
        'port': 1234,
        'password': 'foo',
    }



Registry
~~~~~~~~~
This registry will contain the **states prefix** and **grains prefix** to construct autoinclusion slses files.
It contains also the 'default inclusion status' for any linked states in the **defaults** key.
This registry will load then from configuration the state of inclusion of any included/configured sub state and feed some shortcuts like **actives**, **is** (**has** is a copy/synonym of **is**) and **unactivated** settings.

For example, if you have php disabled as a default, but have installed or enabled it via the pillar, the registry will load it as 'active' thus triggering the autoinclusion of 'php' during an highstate.
This registry may also be queried from any state field to known if a state is active (eg: querying if we are on a devhost by looking if devhost is in the nodetypes registry.

This registry lool like::

    {
        'states_pref': 'makina-states.services',
        'grains_pref': 'makina-states.services',
        'actives': [{'php.fpm':{'active': True} }],
         'unactivated' [{'php.modphp':{'active': False} }],
         'defaults': {
            'php.fpm':{'active': True} },
            'php.modphp':{'active': False},
         }
         'is' : {'modphp': False, 'phpfpm': True},
         'has' : {'modphp': False, 'phpfpm': True},
    }

The default general order of inclusion is as follow:

  - Local settings
  - Controllers
  - Nodes Types
  - Services



