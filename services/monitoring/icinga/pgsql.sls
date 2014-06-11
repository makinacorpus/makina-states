{% set data = salt['mc_icinga.settings']() %}
{% set locs = salt['mc_locations.settings']() %}

{% if data.modules.ido2db.enabled %}
{% if 'pgsql' == data.modules.ido2db.database.type %}

{% import "makina-states/services/db/postgresql/init.sls" as pgsql with context %}

include:
  # if ido2db is enabled, install and configure the sgbd

  # install postgresql
  {% if ((('host' in data.modules.ido2db.database) and (data.modules.ido2db.database.host in ['localhost', '127.0.0.1', grains['host']])) or ('socket' in data.modules.ido2db.database)) %}
  - makina-states.services.db.postgresql
  {% else %}
  - makina-states.services.db.postgresql.hooks
  {% endif %}

# add the user
{{ pgsql.postgresql_user(data.modules.ido2db.database.user,
                         data.modules.ido2db.database.password)}}


{% endif %}
{% endif %}









