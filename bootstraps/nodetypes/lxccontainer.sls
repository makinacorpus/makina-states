#
# See makina-states.nodetypes.lxccontainer
#

{% import "makina-states/_macros/bootstraps.jinja" as bs with context %}

# expose imported macros to callers
{% set funcs = bs.funcs %}
{% set controllers = bs.controllers %}
{% set nodetypes = bs.nodetypes %}

include:
  - {{ nodetypes.statesPref }}lxccontainer

