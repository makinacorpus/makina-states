{%- import "makina-states/services/db/postgresql/hooks.sls" as hooks with context %}
{%- import "makina-states/services/db/postgresql/groups.sls" as groups with context %}
{%- import "makina-states/services/db/postgresql/users.sls" as users with context %}
{%- import "makina-states/services/db/postgresql/dbs.sls" as dbs with context %}
{%- import "makina-states/services/db/postgresql/extensions.sls" as ext with context %}
{#- see doc/ref/formulaes/services/db/postgresql.rst #}
{% set settings = salt['mc_pgsql.settings']() %}
{%- set localsettings = salt['mc_localsettings.settings']() %}
{%- set locs = localsettings.locations %}
{{ salt['mc_macros.register']('services', 'db.postgresql') }}
{%- set default_user = settings.user %}
{#- MAIN #}
include:
  - makina-states.localsettings.locales
  - makina-states.settings.db.postgresql.hooks
  - makina-states.settings.db.postgresql.wrappers
  - makina-states.settings.db.postgresql.prerequisites
  - makina-states.settings.db.postgresql.fix-template-1-encoding
  - makina-states.settings.db.postgresql.pg_hba
  - makina-states.settings.db.postgresql.groups
  - makina-states.settings.db.postgresql.dbs
  - makina-states.settings.db.postgresql.service
  - makina-states.settings.backup.dbsmartbackup
{# api for macro consumers #}
{% set orchestrate = hooks.orchestrate %}
{% set postgresql_db = dbs.postgresql_db %}
{% set postgresql_user = users.postgresql_user %}
{% set postgresql_group = groups.postgresql_group %}
{% set install_pg_exts = ext.install_pg_exts %}
{% set install_pg_ext = ext.install_pg_ext %}
# vim:set nofoldenable:
