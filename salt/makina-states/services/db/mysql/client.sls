{%- import "makina-states/services/db/mysql/hooks.sls" as hooks with context %}
include:
  - makina-states.services.db.mysql.hooks
{%- set orchestrate = hooks.orchestrate %}
{%- set locs = salt['mc_locations.settings']() %}
{% set pkgs = salt['mc_pkgs.settings']() %}
{% set settings = salt['mc_mysql.settings']() %}
{% if settings.client_packages %}
mysql-pkgs-client:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs: {{settings.client_packages}}
    - require:
      - mc_proxy: mysql-pre-install-hook
    - require_in:
      - mc_proxy: mysql-post-install-hook
{% endif %}
