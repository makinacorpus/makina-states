#
# See makina-states.nodetypes.vm
#

{% import "makina-states/_macros/bootstraps.jinja" as bs with context %}

# expose imported macros to callers
{% set controllers = bs.controllers %}
{% set nodetypes = bs.nodetypes %}

include:
  - makina-states.services.dns.bind
  - makina-states.nodetypes.vm

