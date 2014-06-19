uwsgi configuration
===================

See :ref:`mc_module_uwsgi` for configuration options.


Please note that we offer a special macro to generate configurations.

Configurations are enabled and deactivated a la debian, with the /etc/uwsgi/apps-{available/deactivated} directories.
::

{% import "makina-states/services/cgi/uwsgi/init.sls" as uwsgi with context %}
{{ uwsgi.app(name,config_file,config_data,enabled) }}


with

    :name: name of configuration file
    :config_file: template of configuration file
    :config_data: dictionary to fill template
    :enabled: symlink configuration file in /etc/uwsgi/apps-enabled

