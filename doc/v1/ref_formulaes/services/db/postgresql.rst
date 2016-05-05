Postgresql configuration
=========================
This states file aims to configure and manage postgresql clusters
throught their respective unix sockets.

This is common wrappers around **postgresql** states/modules to arrange with
how we manage postgresql clusters (multi versions, layout), that's why
we, again, created our own custom states.

You have:

  postgresql_db
    a macro to define databases with a default group as owner
  postgresql_user
    a macro to define an user, his privileges and groups
  postgresql_group
    a macro to define a group
  postgresql_ext
    a macro to install a single pgsql extension
  postgresql_exts
    a macro to install pgsql extensions


postgresql.conf configuration
-----------------------------
You can override the postgresql.conf by either:
  - attaching to the accumulator (see below)
  - write a file in $CONF_PREFIX/<filename>.conf (except for any default setting in postgresql.conf)
  - editing or overriding the 'pg_conf.<ver>' setting in the pgsql settings
    a (list of dicts), see the mc_states.modules.mc_pgsql module)

PG_HBA configuration
-----------------------
You can override the pg_hba.conf by either:
  - attaching to the accumulator (see below)
  - editing or overriding the 'pg_hba' setting in the pgsql settings
    a (list of dicts), see the mc_states.modules.mc_pgsql module)

Example from pillar

.. code-block:: yaml

   makina.services.postgresql.pg_hba  [ {'type': 'local',
                                       'database': 'foo',
                                       'user': foo', address,
                                       'foo', 'method': 'md5'} ]
   makina.services.postgresql.pg_hba-overrides: [ {...} ]

Example to use the pg_hba block

.. code-block:: yaml

    append-to-pg-hba-{-accumulator:
      file.accumulated:
        - name: pghba-accumulator
        - require_in:
          - file: append-to-pg-hba-block
        - filename: /etc/postgresql/9.3/main/pg_hba.conf
        - text: '# Example from salt !'


Configuration via pillar example
----------------------------------

You can define via pillar the default user to run psql command as:

.. code-block:: yaml

   makina-states.services.postgresql.user: foo (default: postgres)

You can also define in pillar databases and users respecting naming convention:
By default the owner of the database is a group with the same name suffixed
with _owner for the user to be added to. We assign then users to this group

Define a database and its owner as follow (see salt.states.postgres_database.present)

.. code-block:: yaml

    bar-makina-postgresql:
      name: foo (opt, default; 'bar')
      encoding: foo (opt, default; utf8)
      template: foo (opt, default; template0)
      tablespace: foo (opt, default; pg_default)

This will create a 'bar' database owned by the group **bar_owners**

Define a user a follow (see salt.states.postgres_user.present)

.. code-block:: yaml

   bar-makina-services-postgresql-user:
     password: h4x
     groups: bar_owners (opt, default: [])
     encrypted: True (opt, default: True)
     superuser: True (opt, default: False)
     createdb: True (opt, default: False)
     replication: True (opt, default: False)

This will create a bar user with 'h4x' password and in group 'bar-owners' (the one of the precedent database)

eg:

.. code-block:: yaml

   mydb-makina-postgresql: {}
   mydb-makina-services-postgresql-user:
     password: ckan-password
     superuser: True
     groups:
       - mydb_owners

Macro usage examples
--------------------
You can use them in your own states as follow

::

   include:
     - makina-states.services.db.postgresql
   {% import "makina-states/services/db/postgresql/init.sls" as pgsql with context %}
   {% set db_name = dbdata['db_name'] %}
   {% set db_tablespace = dbdata['db_tablespace'] %}
   {% set db_user = dbdata['db_user'] %}
   {% set db_password = dbdata['db_password'] %}
   {{ pgsql.postgresql_db(db_name, tablespace=db_tablespace) }}
   {{ pgsql.postgresql_user(db_user,
                            db_password,
                            groups=['{0}_owners'.format(db_name)]) }}

Remember that states should not contain any secret password or user.
So here for example dbdata would be coming from a default macro
loading pillar data.

Exposed hooks
-------------
The hooks are defined in makina-states.services.db.postgresql-hooks.
{ver} is one of the installed postgresql versions (eg: 9.3)
{db} is a database name

makina-postgresql-pre-base
    before postgresql installation
makina-postgresql-post-base
    after postgresql installation
{ver}-makina-postgresql-pre-create-group
    before installing a group role in a speicific postgresql version
{ver}-makina-postgresql-post-create-group
    before installing a group role in a speicific postgresql version
{ver}-makina-postgresql-pre-create-db
    before databases installation
{ver}-{db}-makina-postgresql-database-post-hook
    specific database post creation hook
{ver}-{db}-makina-postgresql-database-endpost-hook
    specific database post creation hook before creating another database
{ver}-makina-postgresql-post-create-db
    adter databases installation
{ver}-makina-postgresql-pre-create-user
    before installing an user role in a speicific postgresql version
{ver}-makina-postgresql-post-create-user
    after installing an user role in a speicific postgresql version
makina-postgresql-post-inst
    final hook


