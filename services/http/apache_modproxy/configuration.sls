{#
# Install apache & its proxy mode
# Dont forget to include the apache states that you really want
# to trigger the apache installation as we just here
# attach to apache installation & orchestration hooks
#}
{# Adding modules #}

include:
  - makina-states.services.http.apache.hooks
  - makina-states.services.http.apache.services

apache-reverse-proxy:
  mc_apache.include_module:
    - modules:
      - proxy_http
      - rewrite
      - env
    - watch:
      - mc_proxy: makina-apache-post-inst
    - watch_in:
      - mc_proxy: makina-apache-pre-conf
