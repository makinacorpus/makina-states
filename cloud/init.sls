{%- import "makina-states/_macros/funcs.jinja" as funcs with context %}
{# see makina-states.cloud.standalone #}
include:
  - makina-states.cloud.standalone
{# be sure to run at the end of provisionning to commit
 # /etc changes #}
{{funcs.autocommit('cloud')}}
