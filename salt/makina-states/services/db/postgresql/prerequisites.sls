{%- import "makina-states/services/db/postgresql/hooks.sls" as hooks with context %}

include:
  - makina-states.services.db.postgresql.hooks
  - makina-states.services.db.postgresql.client

{%- set ssl = salt['mc_ssl.settings']() %}
{%- set orchestrate = hooks.orchestrate %}
{%- set locs = salt['mc_locations.settings']() %}
{% set pkgs = salt['mc_pkgs.settings']() %}
{% set settings = salt['mc_pgsql.settings']() %}

postgresql-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - python-virtualenv {# noop #}
      {% if grains['os_family'] in ['Debian'] %}
      {% for pgver in settings.versions %}
      - postgresql-{{pgver}}
      - postgresql-server-dev-{{pgver}}
      - postgresql-{{pgver}}-pgextwlist
      {% endfor %}
      - libpq-dev
      - postgresql-contrib
      {% endif %}
    {% if grains['os_family'] in ['Debian'] %}
    - require:
      - pkgrepo: pgsql-repo
      - pkg: postgresql-pkgs-client
      - mc_proxy: {{orchestrate['base']['prepkg']}}
    - require_in:
      - mc_proxy: {{orchestrate['base']['postpkg']}}
    {% endif %}

postpkg-pgtune:
  file.managed:
    - source: "https://raw.githubusercontent.com/makinacorpus/pgtune/515b7bd684c8c157b600b4dbef302ddee4873387/pgtune"
    - name: /usr/local/bin/pgtune
    - user: root
    - group: root
    - mode: 755
    - source_hash: "md5=bbf70e7fb5858f8ec6ca6cc6cb13ad49"
    {% if grains['os_family'] in ['Debian'] %}
    - require:
      - pkgrepo: pgsql-repo
      - pkg: postgresql-pkgs-client
      - mc_proxy: {{orchestrate['base']['prepkg']}}
    - require_in:
      - mc_proxy: {{orchestrate['base']['postpkg']}}
    {% endif %}

pguser-to-ssl-cert:
  user.present:
    - name: postgres
    - optional_groups: [{{ssl.group}}]
    - remove_groups: false
    - require:
      - pkg: postgresql-pkgs
      - mc_proxy: {{orchestrate['base']['prepkg']}}
    - require_in:
      - mc_proxy: {{orchestrate['base']['postpkg']}}
  cmd.wait:
    - watch:
      - user: pguser-to-ssl-cert
    - name: service postgresql restart
    - require:
      - pkg: postgresql-pkgs
      - mc_proxy: {{orchestrate['base']['prepkg']}}
    - require_in:
      - mc_proxy: {{orchestrate['base']['postpkg']}}
