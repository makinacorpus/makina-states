#
# See makina-states.nodetypes.server
#
{% import "makina-states/_macros/bootstraps.jinja" as bs with context %}

# expose imported macros to callers
{% set funcs = bs.funcs %}
{% set controllers = bs.controllers %}
{% set nodetypes = bs.nodetypes %}

include:
  - makina-states.nodetypes.server

