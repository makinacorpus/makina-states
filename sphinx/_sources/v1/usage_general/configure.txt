Configuration
=============

Makina states is a consistent collection of specialized states (or formulaes) that you can
apply to your system to install and configure it.

Our saltstack formulaes (the **sls** files)   leverage the use of saltstack execution modules
(called makina-states registries) to expose
aggregated variables from different configuration sources where the main ones
are the grains and the pillarand the local makina-states registries (msgpack or yaml files inside
/etc/\*salt).

To install something, you can either:

  - set a key/value in pillar or grains (eg: **makina-states.services.http.nginx: true**) and play the highstate
  - Call directly a specific state: **salt-call state.sls makina-states.services.http.nginx**.
    Remember that playing a state may register it and will be called again in
    further highstates.
  - Include directly a specific state in a **include:** sls statement from a
    custom state of yours.

As soon as those states are run, they will set a flag on the machine having
the side effect to register them to be ``auto replayed``
on next highstates, implicitly.

In other word, in the future highstates, they will even run even
if we have not included them explicitly.

To sum up, we have made all of those states reacting and setting tags for the system
to be totally dynamic. All the things you need to do is to set in pillar or in grains
the appropriate values for your machine to be configured.

4 levels are available to make install a ``makina state`` formula.

  - Direct inclusion via the 'include:' statement::

        foo.sls:
            include:
              - include makina-states.services.http.nginx

  - Install directly the state via a salt/salt-call state.sls::

      salt-call state.sls makina-states.services.http.nginx

  - Relevant grain configuration slug::

      salt-call --local grains.setval makina-states.services.http.nginx true
      salt-call state.highstate

  - Relevant pillar configuration slug for the highstate to pick up the newly
    registred state::

          /srv/pillar/foo.sls
          makina-states.services.http.nginx: true in an included  pillar file

You can indeed imagine there is a lot of variables that can be modified to apply the configuration to a minion.
To find what to do, we invite you to just read the states and the documentation that seem to be relevant to your needs.
And to know what flag to modify, find the "python registry" and check the param
to modify, it's always the same dance.

Best practise
--------------
Be careful with grains
~~~~~~~~~~~~~~~~~~~~~~
- Grains can be particulary insecures because they are freely set on the client (minion) side,
- Grains are are slow to update.
- You have to pay attention that states and pillar accesses chained by this inheritance
  are only limited to the scope you want and do not expose too many sensitive
  information because a minion setted a particular grain.

Writing rules
~~~~~~~~~~~~~~

Some rules to write makina-states states:

  - When you create a new state, include it in its respective registry.
  - Avoid to write an absolute path, use localsettings.locations.PATH_PREFIX
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
    slugs will be correctly ordered during execution.
  - If your states are getting being or need scheduling, please add separate hooks (mc.proxy.hook states)
    files (see developer documentation).
