#
# Boostrap an host
#  - install a mastersalt master/minion
#

{% import "makina-states/_macros/bootstraps.jinja" as bs with context %}

# expose imported macros to callers
{% set funcs = bs.funcs %}
{% set controllers = bs.controllers %}
{% set nodetypes = bs.nodetypes %}

include:
  - {{ bs.controllers.statesPref }}mastersalt_master
