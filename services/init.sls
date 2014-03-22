{%- import "makina-states/_macros/funcs.jinja" as funcs with context %}
{# see makina-states.services.standalone #}
include:
  - makina-states.services.standalone

{# be sure to run at the end of provisionning to commit
 # /etc changes #}
{{funcs.autocommit('services')}}
