{%- import "makina-states/services/db/postgresql/hooks.sls" as hooks with context %}

include:
  - makina-states.services.db.postgresql.hooks

{%- set orchestrate = hooks.orchestrate %}
{%- set locs = salt['mc_locations.settings']() %}
{%- set pkgs = salt['mc_pkgs.settings']() %}
{%- set settings = salt['mc_pgsql.settings']() %}
{%- if grains['os_family'] in ['Debian'] %}
pgsql-repo:
  pkgrepo.managed:
    - name: deb http://apt.postgresql.org/pub/repos/apt/ {{settings.dist}}-pgdg main
    - file: {{ locs.conf_dir }}/apt/sources.list.d/pgsql.list
    - keyid: 'ACCC4CF8'
    - keyserver: {{pkgs.keyserver }}
    - require:
      - mc_proxy: {{orchestrate['base']['prepkg']}}
    - require_in:
      - mc_proxy: {{orchestrate['base']['postpkg']}}
{%- endif %}

postgresql-pkgs-client:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - python-virtualenv {# noop #}
      {% if grains['os_family'] in ['Debian'] %}
      {% for pgver in settings.versions %}
      - postgresql-client-{{pgver}}
      {% endfor %}
      - libpq-dev
      {% endif %}
    {% if grains['os_family'] in ['Debian'] %}
    - require:
      - pkgrepo: pgsql-repo
      - mc_proxy: {{orchestrate['base']['prepkg']}}
    - require_in:
      - mc_proxy: {{orchestrate['base']['postpkg']}}
    {% endif %}
