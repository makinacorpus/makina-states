Postgis configuration
======================

Install postgis packages.
Then install a database named **postgis** using makina-states.services.db.postgresql
macros.


Activation
------------
.. code-block:: yaml

    makina-states.services.gis.postgis: true

Use a database with posgis template
-----------------------------------
.. code-block:: yaml

    {%- import "makina-states/services/db/postgresql.sls" as pgsql with context %}
    {{- pgsql.postgresql_db(common.data.db.name, template="postgis") }}
    {{- pgsql.postgresql_user(common.data['db']['user'],
                              password=common.data['db']['password'],
                              db=common.data['db']['name'],) }}


