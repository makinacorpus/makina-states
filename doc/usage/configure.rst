Configuration
=============

Makina states is a consistent collection of states (or formulaes) that you just have to aplly on your system to install and configure a particular services.
To configure a machine and its underlying services via makina-states, we use registries which will feed their exposed variables through different configuration sources where the main ones are the grains and the pillar.

To install something, you can either:

  - set a key/value in pillar or grains (eg: **makina-states.services.http.apache: true**)
  - Call directly a specific state: **salt-call state.sls makina-states.services.http.apache**
  - Include directly a specific state in a **include:** sls statement

As soon as those tags are run, they will set a grain on the machine having the side effect to register that set of states to be 'auto installed' and 'reconfigured' on next highstates, implicitly.
In other word, in the future highstates, they will even run even if we have not included them explicitly.
To sum up, we have made all of those states reacting and setting tags for the system
to be totally dynamic. All the things you need to do is to set in pillar or in grains
the appropriate values for your machine to be configured.

In other words, you have 4 levels to make salt install you a 'makina state'
which will be automaticaly included in the next highstate:

  - Direct inclusion via the 'include:' statement::

        foo.sls:
            include:
              - include makina-states.services.http.apache

  - Install directly the state via a salt/salt-call state.sls::

      salt-call state.sls makina-states.services.http.apache

  - Appropriate grain configuration slug::

      salt-call --local grains.setval makina-states.services.http.apache true
      salt-call state.highstate

  - Appropriate pillar configuration slug::

      /srv/pillar/foo.sls
      makina-states.services.http.apache: true in a pillar file

  - Run the highstate, and as your machine is taggued, apache will be installed

You can imagine that there a a lot of variables that can modify the configurationa applied to a minion.
To find what to do, we invite you to just read the states and the documentation that seem to be relevant to your needs.

Best practise
--------------
Be careful with grains
~~~~~~~~~~~~~~~~~~~~~~
As grains are particulary insecures because they are freely set on the client (minion) side, pay attention that states and pillar accesses chained by this inheritance are only limited to the scope you want and do not expose too many sensitive information.

To better understand how things are done, this is an non exhaustive graph
or our states tree:

Writing rules
~~~~~~~~~~~~~~

Some rules to write makina-states states:

  - When you create a new state, include it in its respective registry
  - Never ever write an absolute path, use localsettings.locations.PATH_PREFIX

      - If your path is not in that mapping and is enoughtly generic, just add it.

  - Try to isolate the settings and make a subregistry to regroup them and expose them cleanly in the respective macro.
  - Never ever use short form of states (states without names, use states unique IDs)

    DO::

        foo-foo:
            cmd.run
                name: /foo/foo

    DONT::

        /foo/foo
            cmd.run: []


  - Please use as much as possible require(_in)/watch(_in) to ensure your configuration
    slugs will be correctly scheduled
  - Use CamelCase for variables names for them to not been marked as jinja private variables
  - On the contrary, use _underscore_case for very private macros variables
  - If your states are getting being or need scheduling, please add separate hooks files (see developer documentation).

TODO:
  - We are planning the uninstall part but it is not yet done
  - In the meantime, to uninstall a state, you ll have first to remove the grain/pillar/inclusion
    Then rerun the highstate and then code a specific cleanup sls file if you want to cleanup
    what is left on the server
