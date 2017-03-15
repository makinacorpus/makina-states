Services kind helpers
======================
This macro leverage the usage of **mc_services** module by having some registry
shortcuts, please have a look at the `code of the macro <https://github.com/makinacorpus/makina-states/blob/master/_macros/services.jinja>`_ to know what settings are
availables.


To use it in your states, just do something like that

.. code-block:: yaml

    {% import "makina-states/_macros/services.jinja" as services with context %}
    foo:
        cmd.run:
            -name: echo {{ services.apacheSettings.mpm}}



