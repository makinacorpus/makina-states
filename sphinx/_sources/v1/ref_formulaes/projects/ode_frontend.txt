Ode frontend project
====================

Repository located at https://github.com/makinacorpus/django-ode.

It uses the python project state.

The following services are included and can be customized through the pillar,
check their respectives documentation for more information on how to do it:

* makina-states.services.db.postgresql
* makina-states.services.http.nginx
* makina-states.localsettings.nodejs
* makina-states.localsettings.python

The following settings can be modified through the pillar:

* makina-states.projects.ode_frontend.db_name
* makina-states.projects.ode_frontend.db_user
* makina-states.projects.ode_frontend.db_password


TODO
----

Add circus service and configure watcher.


