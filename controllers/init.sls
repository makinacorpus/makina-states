{%- import "makina-states/_macros/funcs.jinja" as funcs with context %}
{# see makina-states.controllers.standalone #}
include:
  - makina-states.controllers.standalone

{# be sure to run at the end of provisionning to commit
 # /etc changes #}
{{funcs.autocommit('controllers')}}
