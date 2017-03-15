uwsgi configuration
===================

See :ref:`module_mc_uwsgi` for configuration options.


Please note that we offer a special macro to generate configurations.

Configurations are enabled and deactivated a la debian, with the /etc/uwsgi/apps-{available/deactivated} directories.
::

{% import "makina-states/services/cgi/uwsgi/init.sls" as uwsgi with context %}
{{ uwsgi.config(config_name, config_file, enabled, **kwargs) }}

with

    :config_name: name of configuration file
    :config_file: template of configuration file
    :enabled: if true, symlink configuration file in /etc/uwsgi/apps-enabled



