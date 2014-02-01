{#-
# Install in full mode, see the standalone file !
#}

{%- import "makina-states/services/db/postgresql-standalone.sls" as base with context %}

{% set orchestrate = base.orchestrate %}
{% set services = base.services %}
{% set postgresql_db = base.postgresql_db %}
{% set postgresql_user = base.postgresql_user %}
{% set postgresql_group = base.postgresql_group %}
{% set install_pg_exts = base.install_pg_exts %}
{% set install_pg_ext = base.install_pg_ext %}
{% set postgresql_wrappers = base.postgresql_wrappers %}
{{ base.do_content_from_pillar(full=True) }}
