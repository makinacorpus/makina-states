{%- import "makina-states/services/db/postgresql/hooks.sls" as hooks with context %}

include:
  - makina-states.services.db.postgresql.hooks

{%- set orchestrate = hooks.orchestrate %}
{%- set localsettings = salt['mc_localsettings.settings']() %}
{%- set locs = localsettings.locations %}
{% set settings = salt['mc_pgsql.settings']() %}
{%- if grains['os_family'] in ['Debian'] %}
pgsql-repo:
  pkgrepo.managed:
    - name: deb http://apt.postgresql.org/pub/repos/apt/ {{localsettings.lts_dist}}-pgdg main
    - file: {{ locs.conf_dir }}/apt/sources.list.d/pgsql.list
    - keyid: 'ACCC4CF8'
    - keyserver: {{localsettings.keyserver }}
    - require:
      - mc_proxy: {{orchestrate['base']['prepkg']}}
    - require_in:
      - mc_proxy: {{orchestrate['base']['postpkg']}}
{%- endif %}
postgresql-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - python-virtualenv {# noop #}
      {% if grains['os_family'] in ['Debian'] %}
      {% for pgver in settings.versions %}
      - postgresql-{{pgver}}
      - postgresql-server-dev-{{pgver}}
      {% endfor %}
      - libpq-dev
      - postgresql-contrib
      {% endif %}
    {% if grains['os_family'] in ['Debian'] %}
    - require:
      - pkgrepo: pgsql-repo
      - mc_proxy: {{orchestrate['base']['prepkg']}}
    - require_in:
      - mc_proxy: {{orchestrate['base']['postpkg']}}
    {% endif %}
