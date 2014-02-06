{#
# Install apache & its proxy mode
# Dont forget to include the apache states that you really want
# to trigger the apache installation as we just here
# attach to apache installation & orchestration hooks
#}
{# Adding modules #}

include:
  - makina-states.services.http.apache-hooks

apache-reverse-proxy:
  mc_apache.include_module:
    - modules:
      - proxy_http
      - rewrite
      - env
    - require_in:
      - mc_proxy: makina-apache-pre-conf
