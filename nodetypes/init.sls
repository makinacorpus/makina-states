{%- import "makina-states/_macros/funcs.jinja" as funcs with context %}
{# see makina-states.nodetypes.standalone #}
include:
  - makina-states.nodetypes.standalone

{# be sure to run at the end of provisionning to commit
 # /etc changes #}
{{funcs.autocommit('nodetypes')}}
