 {%- import "makina-states/_macros/localsettings.jinja" as localsettings with context %}
{# see makina-states.nodetypes.standalone #}
include:
  - makina-states.nodetypes.standalone

{# be sure to run at the end of provisionning to commit
 # /etc changes #}
{{localsettings.autocommit('nodetypes')}}
