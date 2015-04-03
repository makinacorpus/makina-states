Configuration
=============

Makina states is a consistent collection of states (or formulaes) that you just
have to apply on your system to install and configure a particular service.
To configure a machine and its underlying services via makina-states,
we use registries which will feed their exposed variables through different
configuration sources where the main ones are the grains and the pillar
and the local makina-states registries (msgpack or yaml files inside
/etc/\*salt).

To install something, you can either:

  - set a key/value in pillar or grains (eg: **makina-states.services.http.nginx: true**)
  - Call directly a specific state: **salt-call state.sls makina-states.services.http.nginx**
  - Include directly a specific state in a **include:** sls statement

As soon as those tags are run, they will set a grain on the machine having
the side effect to register that set of states to be ``auto installed``
and ``reconfigured`` on next highstates, implicitly.
In other word, in the future highstates, they will even run even
if we have not included them explicitly.
To sum up, we have made all of those states reacting and setting tags for the system
to be totally dynamic. All the things you need to do is to set in pillar or in grains
the appropriate values for your machine to be configured.

In other words, you have 4 levels to make salt install you a ``makina state``
formula.
When a formula has run, there is a good change that it will be automaticaly included in the next highstate:

  - Direct inclusion via the 'include:' statement::

        foo.sls:
            include:
              - include makina-states.services.http.nginx

  - Install directly the state via a salt/salt-call state.sls::

      salt-call state.sls makina-states.services.http.nginx

  - Relevant grain configuration slug::

      salt-call --local grains.setval makina-states.services.http.nginx true
      salt-call state.highstate

  - Relevant pillar configuration slug::

      /srv/pillar/foo.sls
      makina-states.services.http.nginx: true in a pillar file

  - Run the highstate, and as your machine is taggued,nginx will be installed

You can imagine that there a a lot of variables that can modify the configurationa applied to a minion.
To find what to do, we invite you to just read the states and the documentation that seem to be relevant to your needs.

Best practise
--------------
Be careful with grains
~~~~~~~~~~~~~~~~~~~~~~
- Grains can be  particulary insecures because they are freely set on the client (minion) side,
- You have to pay attention that states and pillar accesses chained by this inheritance are only limited to the scope you want and do not expose too many sensitive information because a minion setted a particular grain.

Writing rules
~~~~~~~~~~~~~~

Some rules to write makina-states states:

  - When you create a new state, include it in its respective registry.
  - Never ever write an absolute path, use localsettings.locations.PATH_PREFIX
    or another registry variable.
  - Try to isolate the settings and make a subregistry to regroup them.
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
  - If your states are getting being or need scheduling, please add separate hooks files (see developer documentation).
