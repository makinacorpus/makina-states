Python configuration
======================
Help to manage several python versions at once

For ubuntu users, install the deadsnakes repository.

Exposed settings:

    :makina-states.localsettings.python.versions: LIST (default: ["2.4", "2.5", "2.6"]), pythons to install

eg::

    salt-call grains.setval makina-states.localsettings.python.versions '["2.6"]'


