Hooks
=====
Hooks in the makina-states meaning have two functions:

    - Provide a robust orchestration mecanism
    - Provide a way to skip a full subset of states by non inclusion of the real states files during different execution modes (standalone, full).

Those hooks are just states which use the **mc_proxy.hook** function wich does nothing more forward the changes of acendant of the states to the descendant of this state.
For example in::

    one:
        cmd.run:
            - name: /bin/true

    foo:
        mc_hook.proxy:
            - require:
                - cmd: one

    two
        mc_hook.proxy:
            - require:
                - mc_proxy: foo

As one will return a change, foo will also trigger in turn a change, thus two will see foo as 'changed'.

You can also easily skip a full subset of states, imagining the three following files:

- **a.sls**::

    include:
        - hooks

    one:
        cmd.run:
            - name: /bin/true
            - watch_in
                - cmd: one

- **hooks.sls**::

     foo:
        mc_hook.proxy: []


- **c.sls**::

    include:
        - hooks
        {{ if something }}
        - a
        {{ endif }}

    two
        mc_hook.proxy:
            - require:
                - mc_proxy: foo

You just discoved the magic of hooks to make custom execution modes without having to clutter your states files with custom require/includes, you just have to subscribe to isolated hooks, and in the real states files, to also subscribe to those hooks. In the listeners, you just have to conditonnaly include the real state file for the job to be correctly executed with the other states.



