# Boostrap an host which is also a contained VM and not a physical machine
#

{% import "makina-states/_macros/bootstraps.jinja" as bs with context %}

# expose imported macros to callers
{% set controllers = bs.controllers %}
{% set nodetypes = bs.nodetypes %}

include:
  - makina-states.services.dns.bind
  - makina-states.nodetypes.devhost

