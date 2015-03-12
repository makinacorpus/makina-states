Ode api project
================

Repository located at https://github.com/makinacorpus/ODE.

It uses the python project state.

The following services are included and can be customized through the pillar,
check their respectives documentation for more information on how to do it:

* makina-states.services.db.postgresql
* makina-states.localsettings.python

The following settings can be modified through the pillar:

* makina-states.projects.ode_api.db_name
* makina-states.projects.ode_api.db_user
* makina-states.projects.ode_api.db_password
* makina-states.projects.ode_api.circus_port
* makina-states.projects.ode_api.circus_pubsup_port
* makina-states.projects.ode_api.circus_stats_port
* makina-states.projects.ode_api.port
* makina-states.projects.ode_api.admins


TODO
----

Add circus service and configure watcher.


