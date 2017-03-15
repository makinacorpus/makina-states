phantomjs configuration
===========================
see :ref:`module_mc_phantomjs`

Install phantom.js

You can then use the macro to install a specific version of phantomjs in /srv/app/phantomjs/<ver>::

    {% import "makina-states/localsettings/phantomjs/init.sls" as phantomjs with context %}
    {{ phantomjs.install('1.1-beta3', 'sha1_hash') }}


