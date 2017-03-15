Execution modes
~~~~~~~~~~~~~~~~~
**OBSOLETE** We do not use that much execution modes, prefer to split your formulaes in small chunks.
See for example the "makina-states.services.monitoring.supervisor" state.

As we now extensivly use auto inclusion, we are particularly exposed to the **state bloat megalomania** when including a small little state will make rebuild the most part of makina-states. To prevent this, there are 2 main modes of execution and when the full mode will configure from end to end your machine, the standalone mode will skip most of the included states but also some of your currently called sls file.

The main use case is that the first time, you need to install a project and do a lot of stuff, but on the other runs, you just need to pull your new changesets and reload apache.
The full mode is the standart mode, and the **light** mode is called **standalone**.
That's why you ll see most formulaes declined in two sls flavors.

By convention, in those formulaes, we make the **standalone** one as a macro taking at least a **full** boolean parameter and then call it at the end with **full=false**. Then we write the normal sls calling this same little macro with **full=true**.

It is then up to the user of in the other sls includes to choose which sls to apply for the specific use case.

For example, consider the following sls files

- /srv/salt/makina-states/services/awesome/mysuperservice-standalone.sls::

    {% macro do(full=True) %}
    {% if full %}
    OneLongStep:
        super.long: []
    {% endif %}

    OneShortStep:
        super.short []
    {% endmacro %}
    {{ do(full=False) }}

- /srv/salt/makina-states/services/awesome/mysuperservice.sls::

    {% import "makina-states/services/awesome/mysuperservice-standalone.sls" as base with context %}
    {{ do(full=True) }}

By hand, i will do the first time::

    salt-call -lall makina-states.services.awesome.mysuperservice


And in a second time::

    salt-call -lall makina-states.services.awesome.mysuperservice-standalone

As you can guess, OneLongStep will only be called the first time, and OneShortStep will be called both time.

Now, to make the inclusion dynamic in an intermediary sls file, you can also do a condtionnal include::

    include:
        {% if cond %}
        - makina-states.services.awesome.mysuperservice-standalone
        {% else %}
        - makina-states.services.awesome.mysuperservice
        {% endif %}




