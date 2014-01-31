#
# See makina-states.nodetypes.travis
#

{% import "makina-states/_macros/bootstraps.jinja" as bs with context %}

# expose imported macros to callers
{% set funcs = bs.funcs %}
{% set controllers = bs.controllers %}
{% set nodetypes = bs.nodetypes %}


{% import "makina-states/_macros/controllers.jinja" as controllers with context %}
{% import "makina-states/_macros/nodetypes.jinja" as nodetypes with context %}

# expose imported macros to callers
{% set controllers = controllers %}
{% set nodetypes = nodetypes %}

include:
  - makina-states.nodetypes.vagrantvm

