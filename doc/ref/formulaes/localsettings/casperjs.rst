casper configuration
=====================
see :ref:`mc_module_casperjs`

Install casper.js

You can then use the macro::

    {% import "makina-states/localsettings/casperjs/init.sls" as casperjs with context %}
    {{ casperjs.install('1.9.7', 'sha1_hash') }}
