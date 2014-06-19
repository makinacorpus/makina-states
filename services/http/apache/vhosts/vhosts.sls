{% import "makina-states/services/http/apache/macros.sls" as macros with context %}
include:
  - makina-states.services.http.apache.hooks
  - makina-states.services.http.apache.services
{% set apacheSettings = salt['mc_apache.settings']() %}
{#
# Virtualhosts, here are the ones defined in the apache registry
# check the macro definition for the pillar dictionnary keys available. 
# The virtualhosts key is set as the site name, and all keys are given
# to the virtualhost macro.
#apache-default-settings:
#  virtualhosts:
#     example.com:
#        active: False
#        small_name: example
#        number: 200
#        documentRoot: /srv/foo/bar/www
#      example.foo.com:
#        active: False
#        number: 202
#
# Note that the best way to make a VH is not via the registry, but
# loading the macro as we do here and use virtualhost(**kw) call
# in a state.
#}
{% if 'virtualhosts' in apacheSettings %}
{%   for site, siteDef in apacheSettings['virtualhosts'].items() -%}
{%     do siteDef.update({'domain': site}) %}
{{     macros.virtualhost(**siteDef) }}
{%-   endfor %}
{%- endif %}
